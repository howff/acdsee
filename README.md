# ACDSee Photo Database Extraction

ACDSee photo database extraction.

# GUI tools to read the database files

* OpenOffice Base
* DBF Viewer 2000

# Python libraries to read the database files

* dbfread (no longer maintained, but works)
* dbfread2 (maintained, but only works on Python 3.12 or later)
* dbf (not tried)
* dbase3-py (now deprecated in favour of pybase3)
* pybase3 (not tried)
* ybf (not tried)

# Python using dbfread

Some problems encountered:
* It cannot handle unknown field types (ACDSee seems to use field types such as 7 for dates and B)
* It requires the memo files (only some are present)
* It assumes ASCII character encoding (ACDSee seems to use Windows)

Unknown field types - a new Class is implemented to extract them
but the timestamp format has not been decoded yet.

Memo files - dbfread can be told to ignore missing files.

Character encoding - use Code Page 437

dbfread gives unknown field type 7

pybase3 gives unknown field type B

# Other woftware

This can convert the ACDSee XML files:
https://github.com/jannisborn/pyacddb

This can create orphaned XML files:
https://github.com/Emil-AC/ACDSee-Orphanage

# Database tables

## Asset.dbf

NAME,FOLDER_ID,FILE_TP_ID,SIZE,WIDTH,HEIGHT,BPP,IMAGE_TYPE,NUM_PAGES,ISREADONLY,ISHIDDEN,HASASAUDIO,HASEMCPROF,HASEXIFSCN,SORT_ORDER,CAPTION,RATING,NOTES,AUTHOR,FTMODIFIED,FTCREATED,FTACCESSED,ACDDATE,EXIFDATE,LMTSCNCMPL,RECCREDATE,CRC,ATTRS,RPP,RAWDATE,RPPUSED,ISTHMBROT,TAGGED,RSVDBOOL1,RSVDBOOL2,RSVDBOOL3,RSVDMEMO1,RSVDINT1,RSVDINT2,RSVDINT3,ACDDBUPOFF,HASACDDBSC,IMGEDITED,DEVELOPED,ACDONLINE,ACDDBLMT,MDDIRTY,LABEL,GEOLUNDONE,SNAPSHOTS,ISORPHAN,ISREMOTE,LMTFACESCN,FACEEBDPD,LMTKEKWSCN,ASSET_ID,TS

* NAME is the filename
* FOLDER_ID is the directory path id, see Folder.dbf
* RATING is the rating number 1 to 5
* ACDDBUPOFF seems to indicate whether the file has metadata to be embedded (pending)

## Folder.dbf

NAME,FOLD_RT_ID,PRNT_ID,FOLDR_TYPE,IS_EXCLUDE,LASTSCANDT,LAST_PLUS,ATTRS,SORT,ISSORTREV,GROUPSET,ISGROUPREV,GROUPRES,FOLDER_ID,TS

