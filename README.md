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

# Other software

This can convert the ACDSee XML files:
https://github.com/jannisborn/pyacddb

This can create orphaned XML files:
https://github.com/Emil-AC/ACDSee-Orphanage

# Database tables

## Asset.dbf

NAME,FOLDER_ID,FILE_TP_ID,SIZE,WIDTH,HEIGHT,BPP,IMAGE_TYPE,NUM_PAGES,ISREADONLY,ISHIDDEN,HASASAUDIO,HASEMCPROF,HASEXIFSCN,SORT_ORDER,CAPTION,RATING,NOTES,AUTHOR,FTMODIFIED,FTCREATED,FTACCESSED,ACDDATE,EXIFDATE,LMTSCNCMPL,RECCREDATE,CRC,ATTRS,RPP,RAWDATE,RPPUSED,ISTHMBROT,TAGGED,RSVDBOOL1,RSVDBOOL2,RSVDBOOL3,RSVDMEMO1,RSVDINT1,RSVDINT2,RSVDINT3,ACDDBUPOFF,HASACDDBSC,IMGEDITED,DEVELOPED,ACDONLINE,ACDDBLMT,MDDIRTY,LABEL,GEOLUNDONE,SNAPSHOTS,ISORPHAN,ISREMOTE,LMTFACESCN,FACEEBDPD,LMTKEKWSCN,ASSET_ID,TS

* NAME is the filename
* FOLDER_ID is the directory, see Folder.dbf
* RATING is the rating number 1 to 5
* ACDDBUPOFF seems to indicate whether the file has metadata to be embedded (pending)

## Folder.dbf

NAME,FOLD_RT_ID,PRNT_ID,FOLDR_TYPE,IS_EXCLUDE,LASTSCANDT,LAST_PLUS,ATTRS,SORT,ISSORTREV,GROUPSET,ISGROUPREV,GROUPRES,FOLDER_ID,TS

* FOLDER_ID is the id of the folder,
* PRNT_ID is the id of the parent folder

To construct a file path you need to follow all the PRNT_ID until you reach the root folder.

# Sample program using ACDSee database

# ACDSee Rating

Each image can have a rating which is a number 1 to 5. This is stored in the XMP metadata in the file (or in a separate .xmp file).

In previous versions of ACDSee it was stored like this:
```
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.5.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:hdrgm="http://ns.adobe.com/hdr-gain-map/1.0/"
    xmlns:xmpNote="http://ns.adobe.com/xmp/note/"
    xmlns:GCamera="http://ns.google.com/photos/1.0/camera/"
    xmlns:Container="http://ns.google.com/photos/1.0/container/"
    xmlns:Item="http://ns.google.com/photos/1.0/container/item/"
    xmlns:acdsee="http://ns.acdsee.com/iptc/1.0/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/">
   <hdrgm:Version>1.0</hdrgm:Version>
   <xmpNote:HasExtendedXMP>5CFC0FC6E95C3D73662A2A2653F5E31A</xmpNote:HasExtendedXMP>
   <acdsee:caption/>
   <acdsee:datetime>2025-09-14T11:37:26.000</acdsee:datetime>
   <acdsee:author/>
   <acdsee:rating>3</acdsee:rating>
   <acdsee:notes/>
   <acdsee:tagged>False</acdsee:tagged>
   <acdsee:categories/>
   <acdsee:collections/>
   <xmp:Rating>3</xmp:Rating>
   <xmp:Label/>
```
In new versions of ACDSee it is stored like this:
```
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.5.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:hdrgm="http://ns.adobe.com/hdr-gain-map/1.0/"
    xmlns:xmpNote="http://ns.adobe.com/xmp/note/"
    xmlns:GCamera="http://ns.google.com/photos/1.0/camera/"
    xmlns:Container="http://ns.google.com/photos/1.0/container/"
    xmlns:Item="http://ns.google.com/photos/1.0/container/item/"
    xmlns:acdsee="http://ns.acdsee.com/iptc/1.0/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
   hdrgm:Version="1.0"
   xmpNote:HasExtendedXMP="BA73CEF33DBB23D816D2ECDAD7247660"
   acdsee:caption=""
   acdsee:datetime="2025-10-15T18:38:42.000"
   acdsee:author=""
   acdsee:rating="3"
   acdsee:notes=""
   acdsee:tagged="False"
   acdsee:categories=""
   acdsee:collections=""
   acdsee:metadataversion="10"
   xmp:Rating="3"
   xmp:Label="">
```

# Sample program using ACDSee rating

Copy files to a destination folder(*) which
* have been tagged with any star rating in the ACDSee database
* have not already been copied (unless their modification date is newer than the last copy)

(*) the destination folder could be a backup, or it could be a synchronisation folder,
for example for `syncthing` to replicate to another device.

e.g.
```
./syncthing.py --log syncthing.log --days 99999 --prefix=2025-0 --laptop --copy
```

Add `--laptop` to copy from a different source directory.
Add `--copy` to actually perform the copy otherwise only a dry-run listing is displayed.

