# bcdl.py

My first project here on github!

In addition to automating album downloading from bandcamp, this project has also been an excuse for me to learn and utilize sqlite3, regex, and BeautifulSoup. Bandcamp recent broke the functionality of this script, so now it's also an excuse to learn selenium :)

## Goals

The ultimate goal behind this project is to be able to:

1. Sign into bandcamp
2. Build a local database of all music owned, including subscription-gated releases
3. Search through this database and select one or multiple albums
4. Download and unzip these releases in the desired format

## Current state

The original script required that you sign into your bandcamp and manually save your collection as an html file that the script could read and build a database with. As of February 8th, bandcamp started requiring a 'token' to download purchased albums which can only be gathered by signing in. **The script is currently broken** but I'm working on rewriting the core functionality in selenium, which will solve a lot of problems once it's finished

## Planned functionality

I believe that the script should take command-line arguments for `username`, `password`, `MAX_ALBUMS`, `TIMEOUT`, `format` and should have some way specify that the user is looking to search through an existing database rather than rebuilding the database. Perhaps default behavior is to build or update the locally-stored database.

Searching will ideally allow for some advanced options, but for now I think the simplest is a broad string match on artist/album either sorted alphabetically or by 'popularity' (number of people who own the album).

Download pages will be stored in the database, but still require the user to be signed in. It is likely mostly trivial to ie: select to download 10 albums, then iterate through the 10 download pages, adding the actual ZIP URLs to a list to parse through later, and then iterating through that list start-to-finish; alternatively, instead of creating a list to iterate through later, it could load the download page and then download/process the ZIP one-by-one.
