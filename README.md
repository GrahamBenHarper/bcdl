# bcdl.py - Automated Bandcamp Album Downloader

My first project here on github!

Do you have a large bandcamp collection and would prefer to download your releases, but you find bandcamp's native download process to be too slow and cumbersome?

**bcdl** is a project that automates the process of downloading, unzipping, and organizing albums from bandcamp. **bcdl** utilizes selenium to sign into a user's account, create or update a local sqlite3 database of their owned albums, and allows the user to search this database and download one or several albums in the format of their choosing.

## Installation
```
git clone https://github.com/corbin-ch/bcdl.git
cd bcdl
pip install -r requirements.txt
```

## Quick start

### Build your local database
Assuming you own 500 or less releases:

`python bcdl.py --update --max_albums 500`

(equivalent: `python bcdl.py -U -m 500`)

Note that you *should* specify the maximum number of releases to add to the database, otherwise it will default to 100. If you have a very large collection and aren't sure of an exact number, there isn't any harm in entering a number like `99999` on the first run; **the point of using lower numbers and having a smaller default is to save time when doing updates to the database in the future so it doesn't need to scroll through your entire collection each and every time.**

### Search your local database
Searching for the word `haircuts`:

`python bcdl.py -s haircuts` (or `--search`)

Or, display your entire local database organized by popularity:

`python bcdl.py -s`

## CLI arguments

* For the vaporwave enjoyers, `-n` (`--non-english-search`) can be used in place of `-s` to **only** show releases by artists with one or more non-English characters in the artist name.
* `--timeout TIMEOUT` or `-t TIMEOUT` can specify how long to wait until a page is considered loaded, since the script cannot tell when it's hit the bottom of your bandcamp collection. The default is 10 seconds, but you may want to increase this number if you have particularly slow internet speeds.
* `--username 'USERNAME' --password 'PASSWORD'` (or `-u` and `-p`) can be used to pass your username/password, so you don't need to sign in manually. In other words, the script will type your username/password for you, but you'll still need to do any captchas that show up.
* `--format 'FORMAT'` (`-f 'FORMAT'`) can be used to specify the desired download format. You must write your selected format as follows (pick one): `'mp3-v0'`, `'mp3-320'`, `'flac'`, `'aac-hi'`, `'vorbis'`, `'alac'`, `'wav'`, `'aiff-lossless'`. If this is not supplied, **bcdl** will simply prompt to select a format while running.
* `--directory 'DIRECTORY'` (`-d 'DIRECTORY'`) can be used to change the directory that music is *unzipped* and organized into. The default behavior is to organize into `./downloads/Artist/Album/`, alongside the .zip archives, which may be ideal for picard users. However, if you store your music in `/mnt/media/Music`, for example, you could pass `-d '/mnt/media/Music'`
* `--dl-directory 'DIRECTORY'` (or `-dl 'DIRECTORY'`) can be used to specify where you'd like the .zip file(s) to download.

## Misc. notes
* "popularity" (the number next to each release) is bandcamp's reported number for how many users own that release, and is currently the only way that release searches are organized. Future updates may be able to update each release's "popularity" without rebuilding the database from scratch, or allow you to organize search results using different critera.
* When selecting a release to download, you can specify a range of releases or individual releases to download. For example, to download releases 1, 2, 3, 4, 10, 15, 16, and 17, you can type: `1-4 10 15-17` -- just like pacman!
* A keen eye may notice that the sqlite3 database actually stores a lot more data than is currently displayed, such as if a release is marked as  private, or a fan club only release; future updates will make use of this data.

## License
I know, I'm sorry I haven't selected one yet; I will take some time to look them over and select one shortly!
