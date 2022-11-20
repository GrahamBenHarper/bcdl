#!/usr/bin/env python3

from bs4 import BeautifulSoup
import sys
import urllib3
import re
import shutil

with open("bc.html") as fp:
    soup = BeautifulSoup(fp, "html5lib")

#<a class="item-link" href="https://noproblemadigital.bandcamp.com/album/modular-thought" target="_blank">

# for tag in soup.find_all('a'):
#     getClass = tag.get('class')
#     if isinstance(getClass, list):
#         if (getClass[0] == 'item-link'):
#             href = tag.get('href')
#             if href:
#                 print(tag.get('href'))

# for tag in soup.find_all('a', class_='item-link'):
#     href = tag.get('href')
#     if (href):
#         print(href)
#     else:
#         continue

http = urllib3.PoolManager()

# temp is used so we only return the first 4 matches
# find all the spans that have the class redownload-item
# then iterate through them, grabbing out the a href's
# (there will only be one per), and then load each site
# and print it. once it's printed, we need to implement
# the regex at the bottom, which will match https://pop...&quot
# which is most of the address, but we need to swap out
# some of the &amps, i think, otherwise i believe that if
# we attempt to download that 'page,' it will return a zip
# of FLACs

temp = 1
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
