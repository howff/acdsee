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
# Write the CSV properly not just append to file
# Keep CSV sorted
# Add a 'date copied' field to the CSV
# Use a database like sqlite not a CSV?

import argparse
import csv
from datetime import datetime
import os
import re
import shutil
import sys
import time

#srcdir="/mnt/cifs/pictures/ixus"
srcdir="/mnt/cifs/backup_ro/dell9500_backup/Pictures"
destdir="/mnt/cifs/pictures/Pixel_Camera_Sync"
database="synced.csv"
days=100

# ---------------------------------------------------------------------
def relative_dir_to_src(filename):
    return os.path.dirname(filename).replace(srcdir+'/', '')

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

# ---------------------------------------------------------------------
def read_database():
    db = {}
    if not os.path.isfile(database):
        return db
    with open(database) as fd:
        csvr = csv.DictReader(fd)
        for row in csvr:
            db[row['path']] = 1
    return db


# ---------------------------------------------------------------------
def find_files_to_copy(db):
    time_now = time.time()

    files_to_copy=[]
    bytes_to_copy = 0

    prevprinted=None
    for root, dirs, files in os.walk(srcdir):
        for name in files:
            # Ignore if an ACDSee backup directory
            if '[Originals]' in root:
                continue
            # Ignore if not a JPEG file
            if (not name.endswith('.JPG')) and (not name.endswith('.jpg')):
                continue
            # Ignore if this directory has already been copied
            fullpath = os.path.join(root, name)
            dire = relative_dir_to_src(fullpath)
            if dire in db:
                continue
            # Ignore if too old
            if time_now - os.path.getmtime(fullpath) > 86400 * days:
                continue
            # Ignore if too small or too large
            filesize = os.path.getsize(fullpath)
            if filesize < 1024 or filesize > 100*1024*1024:
                continue
            # Ignore if not rated 1..5 in ACDSee
            rating = image_rating(fullpath)
            if not rating:
                continue
            # Add to list
            files_to_copy += [fullpath]
            bytes_to_copy += filesize
            # Display directory if not already displayed
            if dire != prevprinted:
                print('ADD %s' % os.path.dirname(fullpath)+'   ', end='\r')
                prevprinted = dire
    return files_to_copy, bytes_to_copy

# ---------------------------------------------------------------------
parser = argparse.ArgumentParser(description='syncthing wrapper')
parser.add_argument('-v', '--verbose', action="store_true", help='verbose')
parser.add_argument('--copy', action="store_true", help='actually perform the copy (otherwise only lists what will be copied)')
parser.add_argument('--log', action="store", help='store progress in the given log file')
args = parser.parse_args()

if args.log:
    logfd = open(args.log, 'a')
else:
    logfd = open('/dev/null', 'w')

timenow = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
print('%s Starting' % timenow)

print('READING DATABASE')
print('LOAD %s' % database, file=logfd)
db = read_database()

print('FIND FILES TO COPY')
files_to_copy, bytes_to_copy = find_files_to_copy(db)

print()
dirs_to_copy=set()
for file in files_to_copy:
    dire = relative_dir_to_src(file)
    dirs_to_copy.add(dire)

for dire in dirs_to_copy:
    print('COPYDIR %s' % dire)
    print('COPYDIR %s' % dire, file=logfd)
print("Total size to copy = %f MB" % (bytes_to_copy / 1024 / 1024))
print("Total size to copy = %f MB" % (bytes_to_copy / 1024 / 1024), file=logfd)

if not args.copy:
    timenow = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print('%s Finished' % timenow)
    sys.exit(0)

print('CREATE DIRECTORIES')
for dire in dirs_to_copy:
    #print(destdir)
    #print(dire)
    #print('MKDIR %s' % os.path.join(destdir, dire))
    print('MKDIR %s' % os.path.join(destdir, dire), file=logfd)
    os.makedirs(os.path.join(destdir, dire), exist_ok=True)

print('COPY')
for file in files_to_copy:
    dire = relative_dir_to_src(file)
    dire = os.path.join(destdir, dire)
    print('COPY %s -> %s' % (file,dire))
    print('COPY %s -> %s' % (file,dire), logfd)
    shutil.copy2(file, dire)

print('UPDATE DATABASE')
print('UPDATE %s' % database, file=logfd)
with open(database, 'a') as fd:
    for dire in dirs_to_copy:
        # Not properly writing as CSV, need to quote paths containing comma,
        if ',' in dire:
            print('"%s"' % dire, file=fd)
        else:
            print('%s' % dire, file=fd)

timenow = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
print('%s Finished' % timenow)
