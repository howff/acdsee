#!/usr/bin/env python3

import sys
import csv
import glob
import os
from dbfread2 import DBF

rootdir='/mnt/cifs/documents/Backup/ACDSee/170Ult/Default'

from dbfread2 import DBF, FieldParser

class TestFieldParser(FieldParser):
    def parse7(self, field, data):
        #print(field.name, data)
        return data

for dbffile in glob.glob(rootdir + '/Folder.dbf'):
    csvfile = os.path.basename(dbffile) + '.csv'
    print('Extract %s to %s' % (dbffile, csvfile))
    table = DBF(dbffile, parser_class=TestFieldParser, encoding='cp437', ignore_missing_memo=True)
    with open(csvfile, 'w') as csvfd:
        writer = csv.writer(csvfd)
        writer.writerow(table.field_names)
        for record in table:
            writer.writerow(list(record.values()))
