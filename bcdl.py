#!/usr/bin/env python3

from bs4 import BeautifulSoup
import sys
import urllib3
import re
import shutil

with open("bc.html") as fp:
    soup = BeautifulSoup(fp, "html5lib")

albumList = list()

http = urllib3.PoolManager()

temp = 1

def makeItReal(something):
    # https://stackoverflow.com/questions/51885694/how-to-decode-backslash-scapes-strings-in-python
    toReturn = something.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')
    #print(f'{something} being returned as {toReturn}')
    return toReturn

for tag in soup.find_all('span', class_="redownload-item"):
    if (temp == 5):
        pass
    else:
        href = tag.find('a')
        site = href.get('href')
        match = None
        print(site)
        try:
            r = http.request('GET', site)
        except:
            print(f"problem loading {site}")
        try:
            data = str(r.data)
            match = re.findall("https:\/\/popplers5.bandcamp.com/download/album\?enc=flac.+?(?=&quot)", data)
        except:
            match = None
        if (match):
            downloadURL = re.sub("\&amp;", "&", match[0])
            soup = BeautifulSoup(data, "html5lib")
            artist = soup.find('div', class_='artist').get_text()[3:] #remove 'by ' at start
            album = soup.find('div', class_='title').get_text()
            with http.request('GET', downloadURL, preload_content=False) as dl, open(f"{artist} - {album}.zip", 'wb') as out_file:
                shutil.copyfileobj(dl, out_file)
            print(downloadURL)

        temp += 1

# https:\/\/popplers5.bandcamp.com/download/album\?enc=flac.+?(?=&quot) -- regex!!!!
