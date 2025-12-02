#!/usr/bin/env python3
# Look in a colleciton of directories for JPEG files whose EXIF dates don't match the directory name
# e.g.
# Given directories: [ '2025-10-31 halloween party', '2025-11-05 bonfire photos' ]
# the EXIF dates in the JPEG files must match the directory name.
# Note that file in subdirectories only have to match their parent date.
# e.g. 2025-10-31 halloween party/bob's photos/image.jpg has to be 2025:10:31
# If they are not exact but within X days then it's ok
# e.g. 2025-12-31 hogmanay/new year/firstfooter.jpg can be 2026:01:01

# Bugs:
# Due to bugs in the exif library it might ignore some files as having no EXIF when in fact they do

import exif
import argparse
from datetime import datetime, timedelta
import sys
import os
import re

debug = False
report_if_ok = False
warn_non_jpeg = False
warn_within_date_range = False

ignored_files = ['Thumbs.db', 'ZbThumbnail.info', 'breezebrowser.dat']

def process_dir(dirpath):
    dirname = os.path.basename(dirpath)
    if debug: print('Looking in directory: %s' % dirname)
    for root, dirs, files in os.walk(dirpath):
        #print(root,dirs,files)
        currdirname = os.path.basename(root)
        match = re.search('^(2[012][0-9][0-9]-[012][0-9]-[0-3][0-9])', dirname)
        if not match:
            print('ERROR: Not a dated directory: %s' % root)
            continue
        dir_date_as_exif = match[1].replace('-',':')
        if debug: print('Directory name decodes as date: %s' % dir_date_as_exif)
        for filename in files:
            if filename in ignored_files:
                continue
            filepath = os.path.join(root, filename)
            if not filename.endswith('.jpg') and not filename.endswith('.JPG'):
                if warn_non_jpeg: print('WARNING: Not a JPEG: %s' % (filepath))
                continue
            if debug: print('Found filename: %s' % filename)
            with open(filepath, 'rb') as fd:
                # Catch exception ValueError caused by bug https://gitlab.com/TNThieding/exif/-/issues/36
                # (it can't find the real EXIF data, have to assume there isn't any)
                try:
                    exif_image = exif.Image(fd)
                except:
                    print('ERROR: No EXIF in %s' % filepath)
                    continue
                if not exif_image.has_exif:
                    print('ERROR: No EXIF in %s' % filepath)
                    continue
                if debug: print('EXIF tags: %s' % dir(exif_image))
                # Get EXIF dates, e.g. "2013:04:08 22:58:01"
                exif_datetime = exif_image.get('datetime', '')
                exif_datetime_digitized = exif_image.get('datetime_digitized', '')
                exif_datetime_original = exif_image.get('datetime_original', '')
                if debug: print('EXIF datetime: %s' % exif_datetime)
                if debug: print('EXIF datetime digitized: %s' % exif_datetime_digitized)
                if debug: print('EXIF datetime original: %s' % exif_datetime_original)
                # Pick a single date, with Original as preferred date
                if exif_datetime_original:
                    exif_datetime = exif_datetime_original
                elif exif_datetime_digitized:
                    exif_datetime = exif_datetime_digitized
                if not exif_datetime:
                    print('ERROR: No EXIF date in file %s' % filepath)
                    continue
                exif_datetime = exif_datetime.split()[0] # get only date not time
                if not exif_datetime.startswith(dir_date_as_exif):
                    if datetime.strptime(exif_datetime, '%Y:%m:%d') - datetime.strptime(dir_date_as_exif, '%Y:%m:%d') < timedelta(days=3):
                        if warn_within_date_range: print('WARNING: date %s not exact but within 3 days of: %s' % (exif_datetime, filepath))
                        continue
                    print('FIX: Wrong date %s not %s in file %s' % (exif_datetime, dir_date_as_exif, filepath))
                    continue
                if report_if_ok: print('EXIF date OK in %s' % filepath)



if __name__ == '__main__':
    # List of directories given as arguments
    dirs = sys.argv[1:]
    # Current directory, if none given
    if not dirs:
        dirs = [os.getcwd()]
    # Process each directory in turn
    for dirpath in dirs:
        process_dir(dirpath)
