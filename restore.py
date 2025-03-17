#!/usr/bin/env python3

# Read the local database looking for images with "Embed Pending" flag
# and a non-zero Rating (ignore Face embeds)
# and see if the file still exists locally. If so, write EXISTS!
# If no longer on local disk, use same folder path but inside \\saucy2
# and see if it exists there, so it could be restored and embedded,
# but if not there then say NOT THERE

import argparse
import sys
import glob
import os
import shutil
from dbfread2 import DBF, FieldParser

catalogdir="c:\\Users\\arb\\AppData\\Local\\ACD Systems\\Catalogs\\170Ult\\Default"
archivedir="\\\\saucy2\\arb_pictures\\ixus"
localdir="c:\\Users\\arb\\Pictures"
localprefix="\\Users\\arb\\Pictures\\"
do_copy = False
logfile = 'restore.log'
putback_file = 'restore_back.sh'

folder = dict()
folder_parent = dict()

if len(sys.argv)>1:
    if sys.argv[1] == '--copy':
        do_copy = True

def printv(str):
    print(str)
    with open(logfile, 'a') as fd:
        print(str, file=fd)

def read_folders(folder_dbf_filename):
    global folder, folder_parent
    printv('Reading %s' % folder_dbf_filename)
    table = DBF(folder_dbf_filename, parser_class=TestFieldParser, encoding='cp437', ignore_missing_memo=True)
    for record in table:
        folder[record['FOLDER_ID']] = record['NAME']
        folder_parent[record['FOLDER_ID']] = record['PRNT_ID']

def folder_path(id):
    path = ''
    while id != '0.0':
        if id in folder:
            path = os.path.join(folder[id], path)
            id = folder_parent[id]
        else:
            break
    return path

class TestFieldParser(FieldParser):
    def parse7(self, field, data):
        #printv(field.name, data)
        return data

if not os.path.isdir(catalogdir):
    raise Exception("no %s" % catalogdir)
if not os.path.isdir(archivedir):
    raise Exception("no %s" % archivedir)
if not os.path.isdir(localdir):
    raise Exception("no %s" % localdir)

read_folders(os.path.join(catalogdir, 'Folder.dbf'))

files_already_exist = set()
dirs_already_exist = set()
dirs_created = set()
files_restored = set()
files_missing = set()

for dbffile in glob.glob(os.path.join(catalogdir, 'Asset.dbf')):
    printv('Extract %s' % (dbffile))
    table = DBF(dbffile, parser_class=TestFieldParser, encoding='cp437', ignore_missing_memo=True)
    for record in table:
        # Only consider images which have > zero Embed Pending flag (0 and -1 are special)
        if record['ACDDBUPOFF'] > 0:
            # Ignore files which don't have a rating (maybe embed pending = faces)
            if record['RATING'] == 0:
                continue
            #printv('%s %s rating %s' % (folder_path(record['FOLDER_ID']), record['NAME'], record['RATING']))
            filepath = os.path.join(folder_path(record['FOLDER_ID']), record['NAME'])
            if os.path.isfile(filepath):
                files_already_exist.add(filepath)
            else:
                # Copy file from \\saucy2\arb_pictures, embed metadata, then move it back
                archivepath = os.path.join(archivedir, filepath.replace(localprefix,''))
                if os.path.isfile(archivepath):
                    destdir = os.path.dirname(filepath)
                    if os.path.isdir(destdir):
                        dirs_already_exist.add(destdir)
                    else:
                        dirs_created.add(destdir)
                    files_restored.add( (archivepath, filepath) )
                else:
                    files_missing.add(archivepath)


for filepath in sorted(files_already_exist):
    printv('ALREADY EXISTS!! %s' % filepath) # You can embed it yourself using ACDSee's menu

for archivepath in sorted(files_missing):
    printv('CANNOT COPY, MISSING %s' % archivepath)

for archivepath,filepath in sorted(files_restored):
    printv('RESTORE  %s  TO  %s' % (archivepath, filepath))

if not files_restored:
    printv('NOTHING TO RESTORE')

for destdir in sorted(dirs_already_exist):
    printv('RESTORE TO DIR ALREADY EXISTS: %s' % destdir)

if not dirs_already_exist:
    printv('NO DIRS ALREADY EXIST, ALL WILL BE CREATED:')

for destdir in sorted(dirs_created):
    printv('RESTORE TO NEW DIR %s' % destdir)

if do_copy:
    put_back = set()
    for archivepath,filepath in sorted(files_restored):
        printv('RESTORE  %s  TO  %s' % (archivepath, filepath))
        put_back.add('mv  "%s"  "%s"' % (filepath, archivepath))
        destdir = os.path.dirname(filepath)
        os.makedirs(destdir, exist_ok=True)
        shutil.copy2(archivepath, filepath)
    # Write a bash script that can put the modified files back into the archive
    with open(putback_file, 'w') as fd:
        for cmd in put_back:
            print(cmd, file=fd)
        for destdir in dirs_created:
            print('rmdir "%s"' % destdir, file=fd)
else:
    printv('Use the --copy option to actually copy')
