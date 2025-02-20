#!/bin/bash
# Find all recent photos,
#  ignore [Originals] directory
#  ignore if not rated 1..5 in ACDSee
#  copy (with final folder name) to the sync folder
# Run syncthing to have those files copied to the Pixel and hence backed up.
# XXX NB if you have 2024-10-20 My Hols/first day/P1.JPG
# the folder on the Pixel will be "first day" not the My Hols one.
# Also the google photos backup loses the folder structure anyway.

#backupdir="/mnt/cifs/pictures/ixus"
backupdir="/mnt/cifs/backup_ro/dell9500_backup/Pictures"
syncdir="/mnt/cifs/pictures/Pixel_Camera_Sync"

find $backupdir -mtime -1 -type f | while read filename; do
    # Ignore ACDSEE [Originals] directory which is just backups
    if expr match "$filename" ".*\[Originals\].*" >/dev/null; then
        continue
    fi
    # Only consider images with an ACDSee rating of 1..5
    # in case rating tag was added but unset.
    if jhead -v "$filename" 2>/dev/null | grep -q "<acdsee:rating>[1-5]</acdsee:rating>"; then
        dirpath=$(dirname "$filename")
        dir=$(basename "$dirpath")
        echo COPY $filename FROM $dir
        mkdir -p "${syncdir}/${dir}"
        cp -p "$filename" "${syncdir}/${dir}/"
    fi
done
