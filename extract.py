#!/usr/bin/env python3

import sys
import csv
import glob
import os
from dbfread2 import DBF

rootdir='/mnt/cifs/documents/Backup/ACDSee/170Ult/Default'

from dbfread2 import DBF, FieldParser

class TestFieldParser_Simple(FieldParser):
    def parse7(self, field, data):
        #print(field.name, data)
        return data

from datetime import datetime, timedelta, timezone

class TestFieldParser(FieldParser):
    def parse7(self, field, data):
        b = bytearray(data)

        # first 4 bytes is an integer Julian Date Number
        jdn = int.from_bytes(bytearray.fromhex(b.hex()[:8]), byteorder='little', signed=False)
        if jdn == 0: return ''  # prevent the csv filling up with 0 dates

        # last 4 bytes is the number of milliseconds since the start of the day
        msec = int.from_bytes(bytearray.fromhex(b.hex()[8:]), byteorder='little', signed=False)

        # use arbitrary offset to move date calculations into modern era
        # https://stackoverflow.com/questions/64836743/julian-day-number-to-local-date-time-in-python
        dt_Offset = 2400001.000 # 1858-11-17 12:00 (note: the 12 hour addition to align ADCsee date format)
        dt = datetime(1858, 11, 17, tzinfo=timezone.utc) + timedelta(jdn-dt_Offset) + timedelta(seconds=msec // 1000)

        dtString = dt.strftime('%d/%m/%Y %H:%M:%S') # convert to desired time format
        #print(field.name, dtString)
        return dtString


for dbffile in glob.glob(rootdir + '/Folder.dbf'):
    csvfile = os.path.basename(dbffile) + '.csv'
    print('Extract %s to %s' % (dbffile, csvfile))
    table = DBF(dbffile, parser_class=TestFieldParser, encoding='cp437', ignore_missing_memo=True)
    with open(csvfile, 'w') as csvfd:
        writer = csv.writer(csvfd)
        writer.writerow(table.field_names)
        for record in table:
            writer.writerow(list(record.values()))
