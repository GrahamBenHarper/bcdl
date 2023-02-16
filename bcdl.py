# all the selenium goodies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

# selenium exceptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException

from time import sleep

# regex
import re

# sqlite3
import sqlite3

# has it been TIMEOUT seconds without a change in the page? then it
# is loaded.
TIMEOUT = 10

# how long to wait for the user to sign in, in seconds
SIGN_IN_TIMEOUT = 15

# for debug messages & limiting number of albums to load
DEBUG = True
MAX_ALBUMS = 100

if (DEBUG):
    debug_file = open('debug_log', 'a')

DB_LOCATION = "bcdl.db"

shared_driver = webdriver.Firefox()


def main():
    refresh_db()


def sign_in():
    '''Will attempt to sign the user into their bandcamp account, load up
    their collection, and click 'show more.' If sign_in() returns True, that
    means that the driver is now authenticated and loaded into the user's
    collection'''

    # this URL will automatically bring us to the user's collection
    # after signing in
    shared_driver.get("https://bandcamp.com/login?from=fan_page")

    username_field = shared_driver.find_element(by=By.NAME,
                                                value="username-field")
    password_field = shared_driver.find_element(by=By.NAME,
                                                value="password-field")

    # TODO: grab these from either the command line, or allow the user to sign
    #       in on their own w/ the window

    user = ''
    pword = ''
    if (DEBUG):
        with open('user_pass', 'r') as login:
            user = login.readline()
            pword = login.readline()
    username_field.send_keys(user)
    password_field.send_keys(pword)

    password_field.send_keys(Keys.RETURN)

    shared_driver.implicitly_wait(10)

    # check to see if we're signed in every 5 seconds & attempt to click the
    # 'show more' button. it's the user's responsibility to solve any captchas
    # or correct any incorrect passwords
    time_waited = 0
    loaded = False
    while (not loaded):
        try:
            show_more_button = shared_driver.find_element(by=By.CLASS_NAME,
                                                          value="show-more")
            loaded = True
            # TODO: need to verify button clicking try/except stuffs is good
            # 2/11 update: tbh it's hacky but probably fine to call it done
            show_more_button.click()
            show_more_button.click()
        except NoSuchElementException:
            if (time_waited >= SIGN_IN_TIMEOUT):
                return False
            log("INFO", f"No luck, have waited {time_waited} seconds; waiting "
                f"another 5 seconds (max timeout {SIGN_IN_TIMEOUT})")
            time_waited += 5
            sleep(5)
        except ElementNotInteractableException:
            # explanation: generally we need 2 button clicks to load the
            # additional elements. however, it seems that sometimes a single
            # click is enough. if we hit this exception, it means that
            # the webdriver was able to find the element, however after 0 or 1
            # clicks, it is no longer able to find it anymore. this -probably-
            # means that the additional elements have been loaded, therefore
            # we no longer need to click and we can just continue on as if
            # nothing happened
            log("INFO", "Failure with button clicking but i -think- we can continue..")

    # if we made out out of the loop, then we're signed in
    return True


def refresh_db():
    # TODO: maybe could return -1 on failure, and numbers of albums added on
    #       success
    '''Will call sign_in() and add any new albums into the database.
    Will stop after MAX_ALBUMS albums. Returns boolean depending on
    success'''
    # (ie: if you only purchased 5 new albums since the last refresh, there's
    # probably no need to go through all 2000 albums owned)

    create_db()
    if (not sign_in()):
        log("ERROR", "failed to sign in!")
        return False

    # scroll down once every second until the page is fully loaded in.
    # once the page is loaded in, the 'elements' variable will contain
    # a list of every album to parse through
    current_album_count = 1
    previous_album_count = 0
    seconds_counter = 0
    actions = ActionChains(shared_driver)

    # search for <li> blocks with an id that starts with ...
    xpath = "//li[contains(@id, 'collection-item-container_')]"

    while (True):
        elements = shared_driver.find_elements(by=By.XPATH, value=xpath)
        current_album_count = len(elements)

        if (previous_album_count == current_album_count):
            break
        elif (current_album_count > MAX_ALBUMS):
            break

        # TODO: i believe the number of keypresses needed is going to change
        #       depending on the size of the window; maybe i'll have to whip
        #       up some sort of equation that takes window height as input
        #       and spits out the number of keypresses required
        actions.send_keys(Keys.PAGE_DOWN)
        actions.send_keys(Keys.PAGE_DOWN)
        actions.send_keys(Keys.PAGE_DOWN)
        actions.perform()

        seconds_counter += 1
        sleep(1)

        if seconds_counter > TIMEOUT:
            log('INFO', 'resetting seconds_counter; previous/current: ' +
                f'{previous_album_count}/{current_album_count}')

            previous_album_count = current_album_count
            seconds_counter = 0

    # if we've reached this point, our page is all loaded in and we simply need
    # to begin parsing it

    grab_popularity_regex = '\\d+'
    grab_short_page_regex = '(?<=https:\\/\\/).+?(?=\\/album)'
    grab_priv_artist_regex = '(?<=by ).+?(?=\n)'

    # xpath strings
    title_xpath = ".//div[@class='collection-item-title']"
    pop_xpath = ".//div[@class='collected-by']//a[@class='item-link also-link']"
    artist_xpath = ".//div[@class='collection-item-artist']"
    bc_xpath = ".//a[@class='item-link']"

    for element in elements:
        # scrape whether or not the album is private
        # BUG: this will flag any artist/album name containing the word
        #      'PRIVATE' as a private album
        if 'PRIVATE' in element.text:
            is_private = 1
        else:
            is_private = 0

        title_element = element.find_element(by=By.XPATH, value=title_xpath)
        pop_element = element.find_element(by=By.XPATH, value=pop_xpath)
        artist_element = element.find_element(by=By.XPATH, value=artist_xpath)
        bc_element = element.find_element(by=By.XPATH, value=bc_xpath)

        # grab out the full bandcamp link
        bc_long = bc_element.get_attribute('href')

        # grab out album/artist
        if (not is_private):
            album_name = title_element.text
            artist_name = artist_element.text
            # chop off the "by" in "by Artist Name"
            artist_name = artist_name[3:]
        else:
            album_name = element.get_attribute("data-title")
            artist_name = re.findall(grab_priv_artist_regex, element.text)[0]

        # regex out popularity & convert to integer
        # TODO: remove try/except block so we don't have a bare except
        try:
            popularity = []
            popularity = re.findall(grab_popularity_regex, pop_element.text)
            if len(popularity) > 0:
                popularity = int(popularity[0])
            else:
                popularity = 0
        except:
            popularity = 0

        # regex the shortlink out if not private
        # (there is no long link for private releases)
        if (not is_private):
            # TODO: remove try/except to see if it's even necessary
            try:
                bc_short = []
                bc_short = re.findall(grab_short_page_regex, bc_long)
                if len(bc_short) > 0:
                    bc_short = bc_short[0]
                else:
                    bc_short = "ERROR"
            except:
                bc_short = "ERROR"
                log("ERROR", "Failed to grab bc_short out of {bc_long}")
        else:
            bc_short = bc_long

        # grab out 'download' href if it exists
        if 'download' in element.text:
            # first download_page is a 'download' element
            download_page = element.find_element(by=By.PARTIAL_LINK_TEXT,
                                                 value='download')
            # then download_page is converted to a string, containing the link
            download_page = download_page.get_attribute("href")
            add_to_db(artist_name, album_name, popularity, is_private,
                      download_page, bc_long, bc_short)
        else:
            download_page = "ERROR"
            log("ERROR", f"no download present in {element.text}")

        log('INFO', f'artist: {artist_name}, album name: {album_name}, '
            f'private: {is_private}, popularity: {popularity} '
            f'bc link & short: {bc_long} & {bc_short} '
            f' download: {download_page}\n'
            '----------------------------------------------------------')

    shared_driver.quit()
    return True


def create_db():
    '''Creates a table named ALBUM with the properties
       artist, album, popularity, is_private, download_page, bc_long, bc_short
       if it does not already exist'''
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master")
    if (not res.fetchone()):
        log("INFO", "making db")
        run_string = "CREATE TABLE ALBUM(artist_name TEXT, album_name TEXT, "
        run_string += "popularity INTEGER, is_private INTEGER, "
        run_string += "download_page TEXT, bc_long TEXT, bc_short TEXT)"
        cur.execute(run_string)


def is_dl_page_in_db(download_page):
    '''Returns True if the provided download_page is already in the database,
    otherwise false'''
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    res = cur.execute(f"SELECT download_page FROM ALBUM WHERE download_page='{download_page}'")
    if (not res.fetchall()):
        log('INFO', f'{download_page} was not in db, returning False')
        con.close()
        return False
    log('INFO', f'{download_page} was in db, returning True')
    con.close()
    return True


def add_to_db(artist_name, album_name, popularity, is_private, download_page,
              bc_long, bc_short):
    '''Adds provided arguments into the database, as long as download_page is
    not already in the database'''
    # TODO: can bring con and cur outside of the scope of this function &
    # expose it to the rest of the script, instead of constantly open/close
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    data = [artist_name, album_name, popularity, is_private, download_page, bc_long, bc_short]
    if (not is_dl_page_in_db(download_page)):
        cur.execute("INSERT INTO ALBUM VALUES(?, ?, ?, ?, ?, ?, ?)", data)
        con.commit()
        con.close()
        log('INFO', f'{album_name} added to db')
        return True
    else:
        log('INFO', f'{album_name} failed to add to db; probably already in there')
        con.close()
        return False
    log('ERROR, 'f'something went wrong while adding {album_name}!!!')
    con.close()
    return False


# TODO: this function should be updated to take some sort of input. Let's say
# the user wants to search for the string XYZ, or for all albums by a single
# artist, and wants to limit to X results, sort in ascending/descending order
# etc. Perhaps this then can return a download_page list() with each index
# corresponding to the index printed next to each result
def print_db():
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    res = cur.execute("SELECT artist_name FROM ALBUM")
    print(res.fetchall())

    download_pages = list()
    print_list = list()
    index = 1
    search_string = 'SELECT artist_name, album_name, popularity, '
    search_string += 'is_private, download_page FROM ALBUM ORDER BY popularity DESC'

    download_pages.append(None)  # fix index

    for (artist_name, album_name, popularity, is_private,
         download_page) in cur.execute(search_string):
        download_pages.append(download_page)
        print_list.append(f'{index} - {artist_name} - {album_name} ({popularity})')
        index += 1

    for item in print_list[::-1]:
        print(item)

    con.close()


def log(type, message):
    '''Print and record a debug message'''
    message = str(type) + ': ' + str(message)
    if (DEBUG):
        print(message)
        debug_file.write(message + '\n')


if __name__ == "__main__":
    main()
    print_db()
    shared_driver.quit()
    if (DEBUG):
        debug_file.close()
