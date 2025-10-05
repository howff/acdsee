#!/usr/bin/env python3
#
# Utility to manage SyncThing:
#
# Find all recent photos,
#  ignore [Originals] directory
#  ignore if not rated 1..5 in ACDSee
#  copy (with final folder name) to the sync folder
# Run syncthing to have those files copied to the Pixel and hence backed up.
# XXX NB if you have 2024-10-20 My Hols/first day/P1.JPG
# the folder on the Pixel will be "first day" not the My Hols one.
# Also the google photos backup loses the folder structure anyway.

# TO DO!
#  1. the check step should add up file sizes and
#     ask before copying especially if multiple GB.
#  2. check the file date and if it's newer than the last time
#     its directory was copied then copy it (otherwise it would
#     be ignored because it's directory was previously copied).
# Write the CSV properly not just append to file.
# Keep CSV sorted.
# Use a database like sqlite not a CSV?

import argparse
import csv
from datetime import datetime
import os
import re
import shutil
import sys
import tempfile
import time

debug=False
verbose=False
srcdir="/mnt/cifs/pictures/ixus"
srcdir_laptop="/mnt/cifs/backup_ro/dell9500_backup/Pictures"
destdir="/mnt/cifs/pictures/Pixel_Camera_Sync"
max_days=2000          # don't sync anything older than max_days
min_size=1024          # probably not an image
max_size=100*1024*1024 # 100MB is too large for an image
dir_prefix=None        # Use 202 for 2020 onwards, or None to include all dirs and subdirs
database="synced.csv"


# ---------------------------------------------------------------------
def relative_dir_to_src(filename):
    """ Return the directory for filename but without the srcdir prefix """
    return os.path.dirname(filename).replace(srcdir+'/', '')

def test_relative_dir_to_src():
    assert(relative_dir_to_src(os.path.join(srcdir, "me", "you", "file.jpg")) == 'me/you')


# ---------------------------------------------------------------------
def image_rating(filename):
    rating = None
    with open(filename, 'rb') as fd:
        data = fd.read()
        xmp_start = data.find(b'<x:xmpmeta')
        xmp_end = data.find(b'</x:xmpmeta')
        xmp_str = data[xmp_start:xmp_end+12]
        xmp_str = xmp_str.decode()
        match = re.search('<acdsee:rating>(.)</acdsee:rating>', xmp_str)
        if match:
            rating = match.group(1)
            try:
                rating = int(rating)
            except:
                rating = None
    return rating

def test_image_rating():
    assert(image_rating('/dev/null') == None)
    with tempfile.NamedTemporaryFile() as fd:
        fd.write('stuff <x:xmpmeta> stuff <acdsee:rating>3</acdsee:rating> stuff </x:xmpmeta> stuff'.encode())
        fd.flush()
        assert(image_rating(fd.name) == 3)


# ---------------------------------------------------------------------
def read_database(database):
    """ Read synced.csv to get updateddate,path into a dictionary
    indexed by the path and return the dict. """
    db = {}
    if not os.path.isfile(database):
        return db
    with open(database, 'r', newline='') as fd:
        csvr = csv.DictReader(fd, delimiter='\t')
        for row in csvr:
            # N.B. if path appears twice then the subsequent ones
            # override the earlier ones, which is handy because they
            # probably contain a more recent updateddate (although we
            # don't actually check the date, but we could).
            # The DB doesn't store the time so pretend it's the end of the day
            # so that files modified on the same day are ignored.
            db[row['path']] = time.mktime(time.strptime(row['updateddate'], '%Y-%m-%d')) + (864399.0)
    return db

def test_read_database():
    with tempfile.NamedTemporaryFile() as fd:
        fd.write('updateddate\tpath\n2020-02-02\tdir1/dir2\n'.encode())
        fd.flush()
        assert(read_database(fd.name) == {'dir1/dir2': time.strptime('2020-02-02','%Y-%m-%d')})


# ---------------------------------------------------------------------
def find_files_to_copy(db):
    """ Recursively find files under 'srcdir' and return a tuple
    (files_to_copy[path: str], bytes_to_copy[int]). Ignores
    the [Originals] directory, files too small or too large,
    files older than 'max_days', files not .jpg, files without an
    ACDSee rating, and files in a directory which has already
    been synced (passed in 'db') unless file has been modified
    more recently than the previous sync date.
    """
    time_now = time.time()

    files_to_copy=[]
    bytes_to_copy = 0

    prevprinted=None
    for root, dirs, files in os.walk(srcdir):
        if dir_prefix and (root == srcdir):
            dirs[:] = [d for d in dirs if d.startswith(dir_prefix)]
        for name in files:
            # Ignore if an ACDSee backup directory
            if '[Originals]' in root:
                continue
            # Determine file type
            if name.endswith('.JPG') or name.endswith('.jpg'):
                filetype = 'JPEG'
            elif name.endswith('.mp4.xmp'):
                filetype = 'MP4'
            else:
                filetype = 'NONE'
            # Ignore if not a JPEG file or MP4 XMP file
            if filetype == 'NONE':
                continue
            # Ignore if too old (for XMP applies to the XMP not the MP4)
            fullpath = os.path.join(root, name)
            filestat = os.stat(fullpath)
            if (time_now - filestat.st_mtime) > (86400 * max_days):
                if debug: print(f'IGNORE_TOO_OLD {fullpath}')
                continue
            # Ignore if this directory has already been copied,
            # unless the file has been modified since the directory was last copied.
            dire = relative_dir_to_src(fullpath)
            if (dire in db) and (filestat.st_mtime < db[dire]):
                if debug:
                    print(f'IGNORE_ALREADY_SYNCED {fullpath} on {db[dire]} via {dire}')
                    print('  FILE %s' % datetime.fromtimestamp(filestat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))
                    print('  DB   %s' % datetime.fromtimestamp(db[dire]).strftime("%Y-%m-%d %H:%M:%S"))
                continue
            # Ignore if too small or too large (only applies to JPEG)
            if (filetype == 'JPEG') and (filestat.st_size < min_size):
                if debug: print(f'IGNORE_TOO_SMALL ({filestat.st_size}) {fullpath}')
                continue
            if (filetype == 'JPEG') and (filestat.st_size > max_size):
                if debug: print(f'IGNORE_TOO_LARGE ({filestat.st_size}) {fullpath}')
                continue
            # Ignore if not rated 1..5 in ACDSee
            # This check is last because it involves reading the whole file.
            # For MP4 this reads the XMP file not the whole movie.
            rating = image_rating(fullpath)
            if not rating:
                if debug: print(f'IGNORE_NOT_RATED {fullpath}')
                continue
            # For MP4 we now want the actual movie filename
            if filetype == 'MP4':
                fullpath = fullpath.replace('.xmp', '')
                filestat = os.stat(fullpath)
            # Add to list
            files_to_copy += [fullpath]
            bytes_to_copy += filestat.st_size
            if debug: print(f'ADD_FILE {fullpath}')
            # Display directory if not already displayed
            if dire != prevprinted:
                print('ADD_DIR %s' % os.path.dirname(fullpath)+'   ')
                prevprinted = dire
    return files_to_copy, bytes_to_copy


# ---------------------------------------------------------------------
def main():
    global debug, verbose
    global srcdir, max_days, dir_prefix

    parser = argparse.ArgumentParser(description='syncthing wrapper')
    parser.add_argument('-d', '--debug', action="store_true", help='debug (very detailed, explain each file)')
    parser.add_argument('-v', '--verbose', action="store_true", help='verbose (no extra info right now)')
    parser.add_argument('--copy', action="store_true", help='actually perform the copy (otherwise only list what will be copied)')
    parser.add_argument('--log', action="store", help='store progress in the given log file')
    parser.add_argument('--laptop', action="store_true", help='copy from laptop backup instead of file server')
    parser.add_argument('--days', action="store", help=f'only copy files modified within this many days (default {max_days})')
    parser.add_argument('--prefix', action="store", help=f'only copy inside directories with this prefix, e.g. 2021 (default {dir_prefix})')
    args = parser.parse_args()

    if args.debug: debug=True
    if args.verbose: verbose=True

    if args.laptop:
        srcdir = srcdir_laptop
    if args.days:
        max_days = int(args.days)
    if args.prefix:
        dir_prefix = args.prefix

    if args.log:
        logfd = open(args.log, 'a')
    else:
        logfd = open('/dev/null', 'w')

    timenow = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print('%s Starting' % timenow)

    print('READING DATABASE')
    print('LOAD %s' % database, file=logfd)
    db = read_database(database)

    print('FIND FILES TO COPY')
    files_to_copy, bytes_to_copy = find_files_to_copy(db)
    files_to_copy = sorted(files_to_copy)

    print()
    dirs_to_copy=set()
    for file in files_to_copy:
        dire = relative_dir_to_src(file)
        dirs_to_copy.add(dire)
    dirs_to_copy = sorted(dirs_to_copy) # now a list


    for dire in dirs_to_copy:
        print('COPYDIR %s' % dire)
        print('COPYDIR %s' % dire, file=logfd)
    print("Total size to copy = %f MB" % (bytes_to_copy / 1024 / 1024))
    print("Total size to copy = %f MB" % (bytes_to_copy / 1024 / 1024), file=logfd)

    if not args.copy:
        timenow = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        print('%s Finished' % timenow)
        print('Run with --copy next time')
        sys.exit(0)

    print('CREATE DIRECTORIES')
    for dire in dirs_to_copy:
        #print('MKDIR %s' % os.path.join(destdir, dire))
        print('MKDIR %s' % os.path.join(destdir, dire), file=logfd)
        os.makedirs(os.path.join(destdir, dire), exist_ok=True)

    print('COPY')
    for file in files_to_copy:
        dire = relative_dir_to_src(file)
        dire = os.path.join(destdir, dire)
        print('COPY %s -> %s' % (file,dire))
        print('COPY %s -> %s' % (file,dire), file=logfd)
        shutil.copy2(file, dire)

    print('UPDATE DATABASE')
    print('UPDATE %s' % database, file=logfd)
    write_header = False if os.path.isfile(database) else True
    now = datetime.today().strftime('%Y-%m-%d')
    with open(database, 'a') as fd:
        if write_header:
            print('updateddate\tdirectory', file=fd)
        csvw = csv.writer(fd, delimiter='\t')
        for dire in dirs_to_copy:
            csvw.writerow( [now, dire] )

    timenow = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print('%s Finished' % timenow)


# ---------------------------------------------------------------------
if __name__ == '__main__':
    main()
