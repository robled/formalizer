formalizer
==========
A tuxedo for your music files.  This could eat your data. You've been warned.

What?
-------
This is a tool intended to add consistency to your FLAC and MP3 metadata tags as well as the directories and filenames in which they live.  Many folks obsess over audio ripping and compression techniques, but good, consistent tags are hard to find.  

Available digital audio organization software works differently with regards to tags, so a standard that works well with disparate software is preferred.  Compromises will be made.  Sorting is also important, especially via a file browser or command shell.

Tag Specs
---------

 - **Album Artist** should always equal **Artist** unless it's a compilation album, in which case **Artist** equals *Various Artists*
 - **Track Number** should always be zero-padded for sorting and application compatibility
 - **Year** should always be a 4-digit number.  More specificity for the recording date can be difficult to make consistent.  **Year** should always indicate the original album release date.  Re-releases, remasters, etc will be dealt with below.
 - **Title** should append additional information in parenthesis if applicable, such as *(live)* or *(remix)*.  Since metadata tags don't have a spot for additional data of this type, this is the best place to put it.
 - **Album** should append additional information about the release, such as *(2007 remaster)*
 - **Genre** should exist but due to subjectivity can be whatever you want
 - **Disc Number** should not exist.  Some audio software unconditionally splits up multi-disc albums when this data is present, which in the author's opinion is not desirable.  The days of shuffling discs around are over.  If you want to know what disc you're listening to, look it up on Wikipedia.

Cover Art Specs
---------------
All tags should contain a single front cover image.  All album directories should contain the same image stored as *folder.jpg* for application compatibility.

File Name and Directory Specs
-----------------------------
The directory structure should allow for chronological sorting by original album release date.  The file name should be sortable by track order and contain any additional info such as *(live)* or *(remix)*.

Convention:

*Artist/Year - Album (release detail)/Track Number - Title (track detail).flac*

Example:

    King Crimson/
    ├── 1981 - Discipline (2011 DGM 40th Anniversary Edition)
    │   ├── 01 - Elephant Talk.flac
    │   ├── 02 - Frame By Frame.flac
    │   ├── 03 - Matte Kudasai.flac
    │   ├── 04 - Indiscipline.flac
    │   ├── 05 - Thela Hun Ginjeet.flac
    │   ├── 06 - The Sheltering Sky.flac
    │   ├── 07 - Discipline.flac
    │   ├── 08 - Ade Vocal Loop I.flac
    │   ├── 09 - Ade Vocal Loop II.flac
    │   ├── 10 - The Sheltering Sky (Alternative Mix).flac
    │   ├── 11 - Thela Hun Ginjeet (Instrumental Mix).flac
    │   └── folder.jpg
    └── 1984 - Absent Lovers
        ├── 01 - Entry Of The Crims (live).mp3
        ├── 02 - Larks' Tongues In Aspic (Part III) (live).mp3
        ├── 03 - Thela Hun Ginjeet (live).mp3
        ├── 04 - Red (live).mp3
        ├── 05 - Matte Kudasai (live).mp3
        ├── 06 - Industry (live).mp3
        ├── 07 - Dig Me (live).mp3
        ├── 08 - Three Of A Perfect Pair (live).mp3
        ├── 09 - Indiscipline (live).mp3
        ├── 10 - Sartori In Tangier (live).mp3
        ├── 11 - Frame By Frame (live).mp3
        ├── 12 - Man With An Open Heart (live).mp3
        ├── 13 - Waiting Man (live).mp3
        ├── 14 - Sleepless (live).mp3
        ├── 15 - Larks' Tongues In Aspic (Part II) (live).mp3
        ├── 16 - Discipline (live).mp3
        ├── 17 - Heartbeat (live).mp3
        ├── 18 - Elephant Talk (live).mp3
        └── folder.jpg

Installation
------------
Virtualenv recommended!

    pip install mutagen beets Pil-Lite netifaces wget
    git clone https://github.com/robled/formalizer.git
    cp formalizer/beets-config.yaml ~/.config/beets/config.yaml

Usage
-----
formalizer is intended to be used with [beets](http://beets.radbox.org/).  Run beets first to grab metadata from the internet, and then run formalizer to ensure uniformity.

    beet import <album>
    formalizer.py <album>
__

    
    usage: formalizer.py [-h] [-l] [-r] [-g] [-n] [-i] file_dir [file_dir ...]
    
    TAGS.
    
    positional arguments:
      file_dir    Path to file(s)
    
    optional arguments:
      -h, --help  show this help message and exit
      -l          live tracks
      -r          rename album
      -g          mass genre
      -n          normalize filenames
      -i          list info


