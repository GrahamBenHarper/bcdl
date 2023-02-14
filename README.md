# bcdl.py

My first project here on github!

In addition to automating album downloading from bandcamp, this project has also been an excuse for me to learn and utilize sqlite3, regex, and BeautifulSoup. Bandcamp recently broke the functionality of this script, so now it's also an excuse to learn selenium :)

## Goals

The ultimate goal behind this project is to be able to:

1. Sign into bandcamp
2. Build a local database of all music owned, including subscription-gated releases
3. Search through this database and select one or multiple albums
4. Download and unzip these releases in the desired format

## Current state

### 2/23/23 Update

The core functionality (downloading) **is still not implemented**, but a large portion of the rewrite (from BeautifulSoup to selenium) is complete. Bandcamp treats "regular," "private," and "fan club" releases all differently, and there are a handful of bugs associated with this problem (ie: I fix "fan club" releases, and suddenly "private" releases break). That said, I would really prefer to (accurately) scrape all of the important data into the database prior to moving on to download functionality. Once the download functionality is working consistently, I think I'll want to hammer away at implementing various search features. And from there, who knows!

## Planned functionality

I believe that the script should take command-line arguments for `username`, `password`, `MAX_ALBUMS`, `TIMEOUT`, `audio_format` and should have some way specify that the user is looking to search through an existing database rather than rebuilding the database. Perhaps default behavior is to build or update the locally-stored database.

Searching will ideally allow for some advanced options, but for now I think the simplest is a broad string match on artist/album either sorted alphabetically or by 'popularity' (number of people who own the album). I would also like it to work similarly to Arch's pacman.

Download pages will be stored in the database, but (due to some bandcamp changes) will still require the user to be signed in.
