#!/usr/bin/env python3

from bs4 import BeautifulSoup
import sys
import urllib3
import re
import shutil

with open("bc.html") as fp:
    soup = BeautifulSoup(fp, "html5lib")

albumList = list()
dlFormats = ['mp3-v0', 'mp3-320', 'flac', 'aac-hi', 'vorbis', 'alac', 'wav', 'aiff-lossless']
magicMBstart = '(?<='
# magicMBend = '&quot;:{&quot;size_mb&quot;:&quot;)(.*?)(?=.B)'
magicMBend = '&quot;:{&quot;size_mb&quot;:&quot;)(.*?)(?=&quot;)'

# magicMBstart = '&quot;:{&quot;size_mb&quot;:&quot;' # (?<=vorbis&quot;:{&quot;size_mb&quot;:&quot;)(.*)(?=MB)
# magicMBend = ')(.*)(?=.B)'
magicGrabURL = '(?<=https:\/\/popplers5.bandcamp.com\/download\/album\?enc=flac).+?(?=&quot)'
urlStart = 'https://popplers5.bandcamp.com/download/album?enc='


http = urllib3.PoolManager()

temp = 1

def makeItReal(something):
    # https://stackoverflow.com/questions/51885694/how-to-decode-backslash-scapes-strings-in-python
    toReturn = something.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')
    #print(f'{something} being returned as {toReturn}')
    return toReturn

for tag in soup.find_all('span', class_="redownload-item"):
    if (temp == 11):
        pass
    else:
        href = tag.find('a')
        site = href.get('href')
        match = None
        #print(site)
        try:
            r = http.request('GET', site)
        except:
            print(f"problem loading {site}")
        try:
            data = str(r.data)
            # (?<=https:\/\/popplers5.bandcamp.com\/download\/album\?enc=flac).+?(?=&quot)
            # match = re.findall("https:\/\/popplers5.bandcamp.com/download/album\?enc=flac.+?(?=&quot)", data)
            match = re.sub("\&amp;", "&", re.findall(magicGrabURL, data)[0])
        except:
            match = None
        if (match):
            # downloadURL = re.sub("\&amp;", "&", match[0])
            # downloadURL = urlStart + dlFormats[0] + match
            soup = BeautifulSoup(data, "html5lib")
            artist = makeItReal(soup.find('div', class_='artist').get_text()[3:]) #remove 'by ' at start
            album = makeItReal(soup.find('div', class_='title').get_text())
            # albumList.append({'index': temp, 'artist': artist, 'album': album, 'dlURL': downloadURL})
            albumList.append({'index': temp, 'artist': artist, 'album': album})
            for enc in dlFormats:
                albumList[len(albumList)-1][enc + 'DL'] = urlStart + enc + match
                # print(f'I want to do the regex re.findall({magicMBstart} + {enc} + {magicMBend}, data)')
                albumList[len(albumList)-1][enc + 'MB'] = re.findall(magicMBstart + enc + magicMBend, data)[0]

            # with http.request('GET', downloadURL, preload_content=False) as dl, open(f"{artist} - {album}.zip", 'wb') as out_file:
            #     shutil.copyfileobj(dl, out_file)
            #print(downloadURL)

        temp += 1

# I would like to have some sort of menu that shows a list of all of the albums
# or maybe you could search by record label, artist, etc., depending on what info
# is available

# i'm thinking i could do some sort of dictionary of dictionaries, where the keys are a hash of the original href,
# so you could avoid needing to constantly reload the albums' pages, but you wouldn't need to download everything in
# one go unless you -really- wanted to. could also do some sort of search functionality to grab download links
# as previously stated

for item in albumList[::-1]:
    artist = item['artist']
    album = item['album']
    index = item['index']
    dlURL = item['flacDL']
    dlSize = item['flacMB']
    print(f'#{index} - {artist} - {album} (FLAC {dlSize})\n{dlURL}\n')

# print(albumList)
# print(albumList[0]['album'])
# testing = albumList[0]['album']
# https:\/\/popplers5.bandcamp.com/download/album\?enc=flac.+?(?=&quot) -- regex!!!!
