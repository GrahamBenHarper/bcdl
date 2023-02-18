# bcdl.py - Automated Bandcamp Album Downloader

My first project here on github!

**bcdl** is a project that automates the process of downloading albums from bandcamp. **bcdl** utilizes selenium to sign into a user's account, can create or update a local sqlite3 database of their releases, and then allows the user to search their database and download their selected albums. The downloaded albums are unzipped and stored in the ./downloads directory. Currently, the project is in its alpha stage and provides basic functionality, but deeper search and download control is planned for future updates.

## Quick start

Build your local database (assuming that you own 500 or less releases):

`python bcdl.py --user email@here.com --password pass123word --update --max_albums 500`

Search your local database for the word 'haircuts':

`python bcdl.py --user email@here.com --password pass123word --search haircuts`

Or, display your entire local database:

`python bcdl.py --user email@here.com --password pass123word --search`

## What does it do?

The script builds a local sqlite3 database of the user's releases by signing into the user's account via an automated selenium window. It can either build a full database from scratch, or simply read the newest `MAX_ALBUMS` releases.

It can search through that database locally, allowing the user to specify a search string, or no search string to simply view the entire database. The user can select which releases to download via a *pacman-like* interface.

After selecting which releases to download, **bcdl** will sign into the user's account and download each release, one by one, and unzip them approximately as follows:

`./downloads/Artist - Album.zip`

With the songs being unzipped as:

`./downloads/Artist - Album/Artist - Album - ## Song Title.flac`

Note that selecting an audio format is currently not implemented, and seems to default to however you normally download albums from bandcamp.

## How do I use it?

### Signing in

First, you'll need to specify a username/password for either database building/updating or for release downloading. Currently, you can either:

`python bcdl.py --user email@here.com --password pass123word`

or, you may create a file named `user_pass` in the same directory, containing the email on the first line, password on the second, and nothing else in the file:

*./user_pass*

first line: `email@here.com`

second line: `pass123word`

Next, you'll need to pass the `--debug` flag, *and* you'll still need to provide a username/password, but they will be ignored by **bcdl**:

`python bcdl.py --debug --user gibberish --password gibberish`

You may also intentionally enter an incorrect username/password, and simply sign in on your own once the selenium window pops up. You will have `SIGN_IN_WAIT_TIME` seconds to do so, which is 15 seconds by default, but this can be changed via the argument `--sign_in_wait_time`. For example, the following command allows you 60 seconds to sign in manually:

`python bcdl.py --user gibberish --password gibberish --sign_in_wait_time 60`

(in the above example, the login will fail, and you'll have 60 seconds to type in your username/password yourself)

Also of note is that, no matter which way you choose to sign in, you may have to solve a captcha. The point of the `SIGN_IN_WAIT_TIME` variable is to allow time to complete the captcha.

### Database building/updating

Currently, **bcdl** will crash if all you do is attempt to sign in but you don't pass any other arguments. You must provide either the `--update` or `--search` flag. We'll talk about `--update` first:

`--update` takes no arguments, and all it does is attempt to sign in, and build/update a database up to the first `MAX_ALBUMS` albums. The default value for `MAX_ALBUMS` is 100. The name of this variable is a little misleading; it will actually grab *at least* `MAX_ALBUMS` albums, rather than a *maximum* of `MAX_ALBUMS` albums. The `MAX_ALBUMS` may be changed via the `--max_albums` argument.

Let's say you have a total of 1234 releases in your bandcamp account and you would like to build a local database containing all of these releases. You would use a command similar to this:

`python bcdl.py --user email@here.com --password pass123word --update --max_albums 1300`

Let's say a month has passed since you've last updated your local database, and you've since purchased a staggering 150 new albums. Rather than scanning your entire bandcamp collection again, a command like this can be utilized instead:

`python bcdl.py --user email@here.com --password pass123word --update --max_albums 200`

### Searching/downloading

To search the local database of releases, you can use the `--search` flag followed by a keyword or phrase:

`python bcdl.py --user email@here.com --password pass123word --search haircuts`

This search will return all releases where the artist or album name contains the word "haircuts". The results are sorted by popularity, with the most popular release appearing first. Deeper search functionality is planned but not yet implemented.

Once you have the search results, you can select which releases to download. You can specify a range of releases or individual releases to download. For example, to download releases 1, 2, 3, 4, 5, 10, 12, 15, 16, and 17, you can enter the following:

`1-5 12 15-17 10`

The script will then navigate to each download page, download each selected release, and unzip them into the `./downloads` directory. More granular control over the download process is planned but not yet implemented.

If you want to view the entire database, you can run the `--search` flag without a keyword or phrase:

`python bcdl.py --user email@here.com --password pass123word --search`

## Todo

In addition to some planned functionality above, there is a general todo list in `TODO.md`, as well as throughout the code in `bcdl.py` by searching for the words `TODO`, `BUG`, or `NOTE`.
