#!/usr/bin/env python3

# Read the local database looking for images with "Embed Pending" flag
# and a non-zero Rating (ignore Face embeds)
# and see if the file still exists locally. If so, write EXISTS!
# If no longer on local disk, use same folder path but inside \\saucy2
# and see if it exists there, so it could be restored and embedded,
# but if not there then say NOT THERE

import sys
import glob
import os
from dbfread2 import DBF, FieldParser

catalogdir="c:\\Users\\arb\\AppData\\Local\\ACD Systems\\Catalogs\\170Ult\\Default"
archivedir="\\\\saucy2\\arb_pictures\\ixus"
localdir="c:\\Users\\arb\\Pictures"
localprefix="\\Users\\arb\\Pictures\\"

folder = dict()
folder_parent = dict()

def read_folders(folder_dbf_filename):
    global folder, folder_parent
    print('Reading %s' % folder_dbf_filename)
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
        #print(field.name, data)
        return data

if not os.path.isdir(catalogdir):
    raise Exception("no %s" % catalogdir)
if not os.path.isdir(archivedir):
    raise Exception("no %s" % archivedir)
if not os.path.isdir(localdir):
    raise Exception("no %s" % localdir)

read_folders(os.path.join(catalogdir, 'Folder.dbf'))

for dbffile in glob.glob(os.path.join(catalogdir, 'Asset.dbf')):
    print('Extract %s' % (dbffile))
    table = DBF(dbffile, parser_class=TestFieldParser, encoding='cp437', ignore_missing_memo=True)
    for record in table:
        # Only consider images which have non-zero Embed Pending flag
        if record['ACDDBUPOFF'] > 0:
            # Ignore files which don't have a rating (why are they embed pending - faces?)
            if record['RATING'] == 0:
                continue
            #print('%s %s rating %s' % (folder_path(record['FOLDER_ID']), record['NAME'], record['RATING']))
            filepath = os.path.join(folder_path(record['FOLDER_ID']), record['NAME'])
            if os.path.isfile(filepath):
                print('EXISTS!! %s' % filepath)
            else:
                # Copy file from \\saucy2\arb_pictures, embed metadata, then move it back
                print('RESTORE %s' % filepath)
                archivepath = os.path.join(archivedir, filepath.replace(localprefix,''))
                print('  FROM  %s' % archivepath)
                if not os.path.isfile(archivepath):
                    print('    NOT THERE!!!  %s' % archivepath)
