# all the selenium goodies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException

# TODO: can probably utilize selenium's sleep/wait functions instead;
#       need to research them more
from time import sleep

# regex
import re

# either for debugging or slow database building
MAX_ALBUMS = 100

# if the page is fully loaded
TIMEOUT = 10

driver = webdriver.Firefox()

# this URL will automatically bring us to the user's collection once signed in
driver.get("https://bandcamp.com/login?from=fan_page")

username_field = driver.find_element(by=By.NAME, value="username-field")
password_field = driver.find_element(by=By.NAME, value="password-field")

# TODO: grab these from either the command line, or allow the user to sign
#       in on their own w/ the window
username_field.send_keys("username")
password_field.send_keys("password")

password_field.send_keys(Keys.RETURN)

driver.implicitly_wait(10)

# check to see if we're signed in every 5 seconds. it's the user's
# responsibility to solve any captchas or correct any incorrect passwords
loaded = False
while (not loaded):
    try:
        show_more_button = driver.find_element(by=By.CLASS_NAME,
                                               value="show-more")
        loaded = True
    except NoSuchElementException:
        print("No luck, waiting 5sec and trying again")
        sleep(5)


# clicking once does not work as it merely "selects" the button area
show_more_button.click()
show_more_button.click()

# search for <li> blocks with an id that starts with ...
xpath = "//li[contains(@id, 'collection-item-container_')]"


# scroll down once every second until the page is fully loaded in.
# once the page is loaded in, the 'elements' variable will contain
# a list of every album to parse through
album_count = 0
test_counter = 0
done_scrolling = False
actions = ActionChains(driver)
while (not done_scrolling):
    # test_counter resets every 10 seconds; it's used to check essentially
    # 'have we finished loading? or timed out?'
    test_counter += 1
    if test_counter > TIMEOUT:
        test_counter = 0
    actions.send_keys(Keys.PAGE_DOWN)
    actions.send_keys(Keys.PAGE_DOWN)
    actions.send_keys(Keys.PAGE_DOWN)
    actions.perform()
    sleep(1)
    temp = album_count
    elements = driver.find_elements(by=By.XPATH, value=xpath)
    album_count = len(elements)
    if (temp != album_count):
        print(album_count)
        if (album_count > MAX_ALBUMS):
            done_scrolling = True
    else:
        # BUG: i think this is broken. 'temp' needs to reset every TIMEOUT
        #      seconds, not on each cycle, otherwise we could coincidentally
        #      have a moment where nothing loaded & we hit a 10 second marker.
        #      in other words, we need to compare the number of albums TIMEOUT
        #      ago to the number of albums right now.
        if (test_counter == TIMEOUT) and (temp == album_count):
            # it is very likely that we have hit the end of the page
            done_scrolling = True

print("We made it! WWWWWWWWOOOOOOOOOOOOOOOO")

grab_artist_regex = '(?<=by ).+?(?=\n)'

# BUG: the artist regex and looking for 'PRIVATE' can fail due to:
#      1. the name of a song/etc could contain 'PRIVATE,' setting this to True
#      2. the 'by ' could match more than one thing
#      proposed fixes:- perhaps regex for a string strictly named '\nPRIVATE\n'
#                     - count 'by ' matches; if there is more than one then
#                       probably check album, if album is no then use
#                       first match
for element in elements:
    # TODO: capture popularity via 'appears in [POPULARITY] other collections'
    album_name = element.get_attribute("data-title")
    artist_name = re.findall(grab_artist_regex, element.text)[0]
    if 'PRIVATE' in element.text:
        is_private = True
    else:
        is_private = False
    print(f'artist: {artist_name}, album name: {album_name},'
          'private: {is_private}')
    print(element.text)

    if 'download' in element.text:
        # first download_link is a 'download' element
        download_link = element.find_element(by=By.PARTIAL_LINK_TEXT,
                                             value='download')
        # then download_link is converted to a string, containing the link
        download_link = download_link.get_attribute("href")
        print(download_link)
    print('---------------------')
