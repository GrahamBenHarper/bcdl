#!/usr/bin/env python3

from bs4 import BeautifulSoup
# import sys # currently unused
import urllib3
import re
# import shutil # currently unused
import sqlite3
import requests
from zipfile import ZipFile
import os

with open("bc.html") as file:
    soup = BeautifulSoup(file, "html5lib")
file.close()

con = sqlite3.connect("bcdl.db")
cur = con.cursor()

albumList = list()
hrefToParse = list()

download_formats = ['mp3-v0', 'mp3-320', 'flac', 'aac-hi', 'vorbis', 'alac',
                    'wav', 'aiff-lossless']
chosen_format = 'flac'

magicMBstart = '(?<='
magicMBend = '&quot;:{&quot;size_mb&quot;:&quot;)(.*?)(?=&quot;)'

magicGrabURL = '(?<=https:\/\/popplers5.bandcamp.com\/download\/album\?enc=flac).+?(?=&quot)'
urlStart = 'https://popplers5.bandcamp.com/download/album?enc='


http = urllib3.PoolManager()


def createDB():
    res = cur.execute("SELECT name FROM sqlite_master")
    if (not res.fetchone()):
        print("making db")
        runString = "CREATE TABLE ALBUM(artist, album, site, dlURL"
        for format in download_formats:
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
        print(tag)
        if (temp >= 500):
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
    dlList = list()
    pList = list()
    index = 1
    dlList.append(None) # fix index
    for artist, album, dlURL, download_size in cur.execute(f"SELECT artist, album, dlURL, {chosen_format} FROM album ORDER BY artist"):
        dlList.append(dlURL)
        pList.append(f"{index} - {artist} - {album} ({download_size} MB)")
        index += 1
    # Print the list out backwards
    for item in pList[::-1]:
        print(item)

    print("==> Albums to download (eg: 1 2 3, 1-3)")
    userInput = input("==> ").split()
    selList = list()
    rangeList = list()
    for x in userInput:
        if (x.__contains__("-")):
            rangeList.append(x)
        else:
            selList.append(dlList[int(x)])

    # Iterate through the user-provided ranges, and append the download links to selList
    for x in rangeList:
        theRange = x.split("-")
        lowerBound = int(theRange[0])
        upperBound = int(theRange[1])
        print(f"rangelist is {rangeList}; lowerBound is {lowerBound}, upperBound is {upperBound}")
        for y in range(lowerBound, upperBound + 1):
            print(f"attempting selList.append(dlList[{y}])")
            selList.append(dlList[y])

    for item in selList:
        downloadAlbum(urlStart + chosen_format + item)
        print(item)
    #print(dlList[int(userInput)])

def downloadAlbum(url):
    grab_sitem_regex = '(?<=sitem_id=).*'
    sitem_list = re.findall(grab_sitem_regex, url)
    sitem = None
    if (len(sitem_list) > 0):
        sitem = sitem_list[0]
    else:
        # Problem! URL did not contain sitem_id ???
        print(f"Throwing error; no sitem in {url} detected!!")
        return 1
    print(f"trying to download {sitem}")
    # TODO: check to see if downloads/{sitem}.zip exists already or not
    response = requests.get(url, allow_redirects=True)
    if (response.ok and response.status_code == 200):
        with open('downloads/' + sitem + '.zip', 'wb') as f:
            f.write(response.content)
        f.close()
    os.mkdir('downloads/' + sitem)
    with ZipFile('downloads/' + sitem + '.zip', 'r') as zObject:
        zObject.extractall(path='downloads/' + sitem)




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
                soup = BeautifulSoup(data, "html5lib")
                artist = fixUni(soup.find('div', class_='artist').get_text()[3:]) #remove 'by ' at start
                album = fixUni(soup.find('div', class_='title').get_text())

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

print("Choose encoding:")

for encoding in download_formats:
    formatR = encoding.replace("-", "_")
    print(formatR)

chosen_format = input("> ")


createDB()
buildHrefList()
visitPages()
printDB()
con.close()

# https:\/\/popplers5.bandcamp.com/download/album\?enc=flac.+?(?=&quot) -- regex!!!!
