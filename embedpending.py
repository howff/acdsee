#!/usr/bin/env python3

# Read the database and display all files which have Embed Pending flag
# (ACDDBUPOFF non-zero)

import sys
import glob
import os
from dbfread2 import DBF, FieldParser

#catalogdir='/mnt/cifs/documents/Backup/ACDSee/170Ult/Default'
catalogdir="c:\\Users\\arb\\AppData\\Local\\ACD Systems\\Catalogs\\170Ult\\Default"

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
            path = folder[id] + '\\' + path
            id = folder_parent[id]
        else:
            break
    return path

class TestFieldParser(FieldParser):
    def parse7(self, field, data):
        #print(field.name, data)
        return data

read_folders(catalogdir + '/Folder.dbf')

for dbffile in glob.glob(catalogdir + '/Asset.dbf'):
    print('Extract %s' % (dbffile))
    table = DBF(dbffile, parser_class=TestFieldParser, encoding='cp437', ignore_missing_memo=True)
    for record in table:
        if record['ACDDBUPOFF'] > 0:
            #print('%s in %s rating %s' % (record['NAME'], record['FOLDER_ID'], record['RATING']))
            print('%s%s flag %s rating %s' % (folder_path(record['FOLDER_ID']), record['NAME'],
                record['ACDDBUPOFF'], record['RATING']))
