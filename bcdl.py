#!/usr/bin/env python3

from bs4 import BeautifulSoup
import sys
import urllib3
import re
import shutil
import sqlite3

with open("bc.html") as fp:
    soup = BeautifulSoup(fp, "html5lib")
fp.close()

con = sqlite3.connect("bcdl.db")
cur = con.cursor()

albumList = list()
hrefToParse = list()

dlFormats = ['mp3-v0', 'mp3-320', 'flac', 'aac-hi', 'vorbis', 'alac', 'wav', 'aiff-lossless']
magicMBstart = '(?<='
# magicMBend = '&quot;:{&quot;size_mb&quot;:&quot;)(.*?)(?=.B)'
magicMBend = '&quot;:{&quot;size_mb&quot;:&quot;)(.*?)(?=&quot;)'

# magicMBstart = '&quot;:{&quot;size_mb&quot;:&quot;' # (?<=vorbis&quot;:{&quot;size_mb&quot;:&quot;)(.*)(?=MB)
# magicMBend = ')(.*)(?=.B)'
magicGrabURL = '(?<=https:\/\/popplers5.bandcamp.com\/download\/album\?enc=flac).+?(?=&quot)'
urlStart = 'https://popplers5.bandcamp.com/download/album?enc='


http = urllib3.PoolManager()


def createDB():
    res = cur.execute("SELECT name FROM sqlite_master")
    if (not res.fetchone()):
        print("making db")
        runString = "CREATE TABLE ALBUM(artist, album, site, dlURL"
        for format in dlFormats:
            formatR = format.replace("-", "_")
            runString += f", {formatR}"
        cur.execute(runString + ")")

def fixUni(inputString):
    # https://stackoverflow.com/questions/51885694/how-to-decode-backslash-scapes-strings-in-python
    outputString = inputString.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')
    #print(f'{inputString} being returned as {outputString}')
    return outputString

def buildHrefList():
    temp = 1
    for tag in soup.find_all('span', class_="redownload-item"):
        if (temp >= 10):
            pass
        else:
            href = tag.find('a')
            site = href.get('href')
            hrefToParse.append(site)
            temp += 1

def siteInDB(site):
    res = cur.execute(f"SELECT site FROM album WHERE site='{site}'")
    if (not res.fetchall()):
        return False
    return True

def toMB(value):
    if(value[-2] == 'M'):
        return float(value[:-2])
    elif(value[-2] == 'G'):
        return float(value[:-2]) * 1024
    else:
        return -1

def addToDB(artist, album, site, dlURL, mp3_v0, mp3_320, flac, aac_hi, vorbis, alac, wav, aiff_lossless):
    data = [artist, album, site, dlURL, mp3_v0, mp3_320, flac, aac_hi, vorbis, alac, wav, aiff_lossless]
    if (not siteInDB(site)):
        cur.execute("INSERT INTO album VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        con.commit()
        print(f"{album} added to db")
        return True
    else:
        print(f"{album} failed to add to db; already in there?")
        return False

def printDB():
    res = cur.execute("SELECT artist FROM album")
    print(res.fetchall())
    for row in cur.execute("SELECT artist, album, dlURL, flac FROM album ORDER BY mp3_v0"):
        print(row)

def visitPages():
    for site in hrefToParse:
        match = None
        #print(site)
        if(not siteInDB(site)):
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
                artist = fixUni(soup.find('div', class_='artist').get_text()[3:]) #remove 'by ' at start
                album = fixUni(soup.find('div', class_='title').get_text())
                # albumList.append({'index': temp, 'artist': artist, 'album': album, 'dlURL': downloadURL})
                albumList.append({'index': len(albumList) + 1, 'artist': artist, 'album': album, 'dlURL': match})
                #for enc in dlFormats:
                    #albumList[len(albumList)-1][enc + 'DL'] = urlStart + enc + match
                    # print(f'I want to do the regex re.findall({magicMBstart} + {enc} + {magicMBend}, data)')
                #    albumList[len(albumList)-1][enc] = toMB(re.findall(magicMBstart + enc + magicMBend, data)[0])

                mp3_v0 = toMB(re.findall(magicMBstart + 'mp3-v0' + magicMBend, data)[0])
                mp3_320 = toMB(re.findall(magicMBstart + 'mp3-320' + magicMBend, data)[0])
                flac = toMB(re.findall(magicMBstart + 'flac' + magicMBend, data)[0])
                aac_hi = toMB(re.findall(magicMBstart + 'aac-hi' + magicMBend, data)[0])
                vorbis = toMB(re.findall(magicMBstart + 'vorbis' + magicMBend, data)[0])
                alac = toMB(re.findall(magicMBstart + 'alac' + magicMBend, data)[0])
                wav = toMB(re.findall(magicMBstart + 'wav' + magicMBend, data)[0])
                aiff_lossless = toMB(re.findall(magicMBstart + 'aiff-lossless' + magicMBend, data)[0])
                addToDB(artist, album, site, match, mp3_v0, mp3_320, flac, aac_hi, vorbis, alac, wav, aiff_lossless)

                # with http.request('GET', downloadURL, preload_content=False) as dl, open(f"{artist} - {album}.zip", 'wb') as out_file:
                #     shutil.copyfileobj(dl, out_file)
                #print(downloadURL)


# I would like to have some sort of menu that shows a list of all of the albums
# or maybe you could search by record label, artist, etc., depending on what info
# is available

# i'm thinking i could do some sort of dictionary of dictionaries, where the keys are a hash of the original href,
# so you could avoid needing to constantly reload the albums' pages, but you wouldn't need to download everything in
# one go unless you -really- wanted to. could also do some sort of search functionality to grab download links
# as previously stated

createDB()
buildHrefList()
visitPages()
printDB()
con.close()

# for item in albumList[::-1]:
#      artist = item['artist']
#      album = item['album']
#      index = item['index']
#      dlURL = item['dlURL']
#      dlSize = item['flacMB']
#      print(f'#{index} - {artist} - {album} (FLAC {dlSize}MB)\n{dlURL}\n')

# with open('bcdl.db', 'w') as f:
#    for item in albumList[::-1]:
#        f.write(json.dumps(item))
#        artist = item['artist']
#        album = item['album']
#        index = item['index']
#        dlURL = item['flacDL']
#        dlSize = item['flacMB']
#        print(f'#{index} - {artist} - {album} (FLAC {dlSize})\n{dlURL}\n')
# f.close()

# print(albumList)
# print(albumList[0]['album'])
# testing = albumList[0]['album']
# https:\/\/popplers5.bandcamp.com/download/album\?enc=flac.+?(?=&quot) -- regex!!!!
