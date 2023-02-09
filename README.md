# bcdl.py

(NOTE: I wouldn't even consider this project to be in an 'alpha' phase; currently it's just a tool I'm using to automate some music downloading from bandcamp and is essentially a novelty)

My first project here on github!

In addition to automating downloading some albums from bandcamp, this project has also been an excuse for me to learn and utilize, sqlite3, regex, and BeautifulSoup.

## Goals

The ultimate goal behind this project is to be able to:

1. Sign into bandcamp
2. Build a local database of all music owned, including subscription-gated releases
3. Search through this database and select one or multiple albums
4. Download and unzip these releases in the desired format

## Current state

At this time, the project requires that you sign into bandcamp in a browser and save your collection as a file named `bc.html`. This file will be read by the script.

To do this, simply open up your collection, click "view all X items," and scroll all the way to the very bottom to load in all of the different releases. Once everything is loaded, you can save this page (I believe CTRL-S should work in most browsers). Name it `bc.html` and place it in the same directory as this script.

## Known problems

1. As of Febuary 8th, the server bandcamp uses for serving up ZIP files has changed, which has broken the script. This may be a simple fix but I just wanted to whip up a quick README.md before logging off for the day. I will be fixing this shortly

2. The script cannot download subscription-gated releases, as these require the user to be signed in
