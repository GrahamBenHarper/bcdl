# selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException

from time import sleep

# regex & sqlite
import re
import sqlite3

# downloading & file handling
import requests
from zipfile import ZipFile
import os

# argument & string parsing
import argparse
import urllib.parse


def main():
    GLOBALS = set_global_vars()

    shared_db_con = init_db_con(GLOBALS)

    if GLOBALS['update']:
        shared_driver = init_driver()
        total_added_to_db = refresh_db(shared_driver, GLOBALS, shared_db_con)
        if (total_added_to_db == -1):
            print("Unable to update database! Exiting...")
            exit(1)

    if (GLOBALS['search'] is not None):
        if GLOBALS['non-english'] == True:
            download_list = search_db_non_english(GLOBALS, shared_db_con)
        else:
            download_list = search_db(GLOBALS, shared_db_con)
        print("==> Albums to download (eg: 1 2 3, 1-3)")
        user_input = input("==> ").split()
        selected_list = []
        range_list = []
        for item in user_input:
            if "-" in item:
                range_list.append(item)
            else:
                selected_list.append(download_list[int(item)])

        for item in range_list:
            lower_bound, upper_bound = map(int, item.split("-"))
            for i in range(lower_bound, upper_bound + 1):
                selected_list.append(download_list[i])

        select_format(GLOBALS)
        shared_driver = init_driver()
        download_albums(selected_list, './downloads/', shared_driver, GLOBALS)

    if (GLOBALS['update']):
        print(f"A total of {total_added_to_db} albums were added to the database")

    close_db(GLOBALS, shared_db_con)


def set_global_vars():
    GLOBALS = {}

    GLOBALS['DEBUG_FILE'] = None

    parser = argparse.ArgumentParser()
    parser.add_argument("--username", "-u", dest="username", type=str, default=None,
                        help="Username for signing into Bandcamp")
    parser.add_argument("--password", "-p", dest="password", type=str, default=None,
                        help="Password for signing into Bandcamp")
    parser.add_argument("--update", "-U", dest="update", action="store_true", default=False,
                        help="Refresh the database of purchased music")
    parser.add_argument("--search", "-s", dest="search", type=str, nargs='?', default=None,
                        const='', help="Search for albums in the database")
    parser.add_argument("--non-english-search", "-n", dest="non_english_search", type=str, nargs='?', const='',  default=False,
                        help="Search for albums in the database that contain non-English characters")
    parser.add_argument("--dry", dest="dry_run", action="store_true", default=False,
                        help="Perform a dry run without making any changes")
    parser.add_argument("--db", dest="db", type=str, default="bcdl.db",
                        help="Location of the SQLite database")
    parser.add_argument("--timeout", "-t", dest="timeout", type=int, default=10,
                        help="Timeout between db update checks (see docs)")
    parser.add_argument("--debug", dest="debug", action="store_true", default=False,
                        help="Turn on debugging output")
    parser.add_argument("--max_albums", "-m", dest="max_albums", type=int, default=100,
                        help="Maximum number of albums to retrieve")
    parser.add_argument("--format", "-f", dest="format", type=str, default=None,
                        help="Format to download albums in")
    parser.add_argument("--directory", "-d", dest="directory", type=str, default="./downloads/",
                        help="Music directory to extract into")

    args = parser.parse_args()

    GLOBALS['USER'] = args.username
    GLOBALS['PASS'] = args.password
    GLOBALS['update'] = args.update
    GLOBALS['search'] = args.search
    GLOBALS['non-english'] = args.non_english_search
    if GLOBALS['search'] is None:
        GLOBALS['search'] = args.non_english_search
        GLOBALS['non-english'] = True
    GLOBALS['DRY_RUN'] = args.dry_run
    GLOBALS['DB_LOCATION'] = args.db
    GLOBALS['PAGE_LOAD_TIMEOUT'] = args.timeout
    GLOBALS['DEBUG'] = args.debug

    GLOBALS['MAX_ALBUMS'] = args.max_albums
    GLOBALS['format'] = args.format
    GLOBALS['directory'] = args.directory

    if (GLOBALS['update'] == False) and GLOBALS['search'] == None:
        print("Neither --update nor --search passed; exiting")
        exit()

    return GLOBALS


def init_driver():
    shared_driver = webdriver.Firefox()
    return shared_driver


def sign_in(shared_driver, GLOBALS):
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

    if (GLOBALS['DEBUG']):
        with open('user_pass', 'r') as login:
            GLOBALS['USER'] = login.readline()
            GLOBALS['PASS'] = login.readline()

    if (GLOBALS['USER'] is not None) and (GLOBALS['PASS'] is not None):
        username_field.send_keys(GLOBALS['USER'])
        password_field.send_keys(GLOBALS['PASS'])
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
            show_more_button.click()
            show_more_button.click()
        except NoSuchElementException:
            if (time_waited >= 300):
                return False
            log("INFO", f"No luck, have waited {time_waited} seconds; waiting "
                "another 5 seconds (max wait 300)",
                GLOBALS)
            time_waited += 5
            sleep(5)
        except ElementNotInteractableException:
            log("INFO", "Failure with button clicking, continuing...", GLOBALS)

    # if we made out out of the loop, then we're signed in
    return True


def refresh_db(shared_driver, GLOBALS, shared_db_con):
    '''Will call sign_in() and add any new albums into the database.
    Will stop after MAX_ALBUMS albums. Returns boolean depending on
    success'''
    # (ie: if you only purchased 5 new albums since the last refresh, there's
    # probably no need to go through all 2000 albums owned)

    create_db(GLOBALS, shared_db_con)
    if (not sign_in(shared_driver, GLOBALS)):
        log("ERROR", "failed to sign in!", GLOBALS)
        return -1

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
        elif (current_album_count > GLOBALS['MAX_ALBUMS']):
            break

        actions.send_keys(Keys.PAGE_DOWN)
        actions.send_keys(Keys.PAGE_DOWN)
        actions.send_keys(Keys.PAGE_DOWN)
        actions.perform()

        seconds_counter += 1
        sleep(1)

        if seconds_counter > GLOBALS['PAGE_LOAD_TIMEOUT']:
            log('INFO', 'resetting seconds_counter; previous/current: ' +
                f'{previous_album_count}/{current_album_count}', GLOBALS)

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

    return_album_counter = 0

    # attempt to parse {len(elements)} releases
    for element in elements:
        # scrape whether or not the album is private
        element_text = element.text.split('\n')
        if element_text[2] == 'PRIVATE':
            is_private = 1
        else:
            is_private = 0

        title_element = element.find_element(by=By.XPATH, value=title_xpath)

        try:
            pop_element = element.find_element(by=By.XPATH, value=pop_xpath)
            # regex out popularity & convert to integer
            popularity = []
            popularity = re.findall(grab_popularity_regex, pop_element.text)
            if len(popularity) > 0:
                popularity = int(popularity[0])
            else:
                popularity = 0
        except NoSuchElementException:
            popularity = 0

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


        # regex the shortlink out if not private
        # (there is no long link for private releases)
        if (not is_private):
            bc_short = []
            bc_short = re.findall(grab_short_page_regex, bc_long)
            if len(bc_short) > 0:
                bc_short = bc_short[0]
            else:
                bc_short = "ERROR"
            #except:
            #    bc_short = "ERROR"
            #    log("ERROR", "Failed to grab bc_short out of {bc_long}", GLOBALS)
        else:
            bc_short = bc_long

        # grab out 'download' href if it exists
        if 'download' in element.text:
            # first download_page is a 'download' element
            download_page = element.find_element(by=By.PARTIAL_LINK_TEXT,
                                                 value='download')
            # then download_page is converted to a string, containing the link
            download_page = download_page.get_attribute("href")
            if (add_to_db(artist_name, album_name, popularity, is_private,
                          download_page, bc_long, bc_short, GLOBALS,
                          shared_db_con)):
                return_album_counter += 1
        else:
            download_page = "ERROR"
            log("ERROR", f"no download present in {element.text}", GLOBALS)

        log('INFO', f'artist: {artist_name}, album name: {album_name}, '
            f'private: {is_private}, popularity: {popularity} '
            f'bc link & short: {bc_long} & {bc_short} '
            f' download: {download_page}\n'
            '----------------------------------------------------------',
            GLOBALS)

    shared_driver.quit()
    # NOTE: {len(elements) - return_album_counter} failures,
    #       {return_album_counter} releases added to db
    return return_album_counter


def init_db_con(GLOBALS):
    return sqlite3.connect(GLOBALS['DB_LOCATION'])


def close_db(GLOBALS, shared_db_con):
    shared_db_con.close()


def create_db(GLOBALS, shared_db_con):
    '''Creates a table named ALBUM with the properties
       artist, album, popularity, is_private, download_page, bc_long, bc_short
       if it does not already exist'''
    cur = shared_db_con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master")
    if (not res.fetchone()):
        log("INFO", "making db", GLOBALS)
        run_string = "CREATE TABLE ALBUM(artist_name TEXT, album_name TEXT, "
        run_string += "popularity INTEGER, is_private INTEGER, "
        run_string += "download_page TEXT, bc_long TEXT, bc_short TEXT)"
        cur.execute(run_string)


def is_dl_page_in_db(download_page, GLOBALS, shared_db_con):
    '''Returns True if the provided download_page is already in the database,
    otherwise false'''
    cur = shared_db_con.cursor()
    res = cur.execute(f"SELECT download_page FROM ALBUM WHERE download_page='{download_page}'")
    if (not res.fetchall()):
        log('INFO', f'{download_page} was not in db, returning False', GLOBALS)
        return False
    log('INFO', f'{download_page} was in db, returning True', GLOBALS)
    return True


def add_to_db(artist_name, album_name, popularity, is_private, download_page,
              bc_long, bc_short, GLOBALS, shared_db_con):
    '''Adds provided arguments into the database, as long as download_page is
    not already in the database. Returns True on success, False on failure'''
    # TODO: maybe add some type of option to check if any of this data has
    # been updated (ie: popularity or private settings)
    cur = shared_db_con.cursor()
    data = [artist_name, album_name, popularity, is_private, download_page, bc_long, bc_short]
    if (not is_dl_page_in_db(download_page, GLOBALS, shared_db_con)):
        cur.execute("INSERT INTO ALBUM VALUES(?, ?, ?, ?, ?, ?, ?)", data)
        shared_db_con.commit()
        log('INFO', f'{album_name} added to db', GLOBALS)
        return True
    else:
        log('INFO', f'{album_name} failed to add to db; probably already in there', GLOBALS)
        return False
    log('ERROR, 'f'something went wrong while adding {album_name}!!!', GLOBALS)
    return False


def select_format(GLOBALS):
    '''Will verify if the current value of GLOBALS['format'] is a valid selection
    and, if not, will prompt the user for a valid selection.'''
    formats = ['mp3-v0', 'mp3-320', 'flac', 'aac-hi', 'vorbis', 'alac', 'wav', 'aiff-lossless']
    if GLOBALS['format'] in formats:
        return

    for index, format in enumerate(formats[::-1], start=1):
        print(f"{index} - {format}")
    
    print("==> Audio format to download (eg: 1, 2, ... {})".format(len(formats)))
    while True:
        try:
            user_input = int(input("==> "))
            if 1 <= user_input <= len(formats):
                GLOBALS['format'] = formats[::-1][user_input - 1]
                return
            else:
                print("==> Please enter a number between 1 and {}.".format(len(formats)))
        except ValueError:
            print("==> Please enter a number between 1 and {}.".format(len(formats)))


def search_db_non_english(GLOBALS, shared_db_con):
    cur = shared_db_con.cursor()

    download_pages = list()
    print_list = list()
    index = 1
    sqlite_query = '''
        SELECT artist_name, album_name, popularity, is_private, download_page
        FROM album
        WHERE artist_name GLOB ? AND (artist_name LIKE ? OR album_name LIKE ?)
        ORDER BY popularity DESC
    '''

    download_pages.append(None)  # fix index

    search_pattern = ('*[^a-zA-Z0-9 ,.!?-]*')
    search_string = '%' + GLOBALS['search'] + '%'
    sqlite_result = cur.execute(sqlite_query, (search_pattern, search_string, search_string)).fetchall()

    for (artist_name, album_name, popularity, is_private,
         download_page) in sqlite_result:
        download_pages.append(download_page)
        print_list.append(f'{index} - {artist_name} - {album_name} ({popularity})')
        index += 1

    for item in print_list[::-1]:
        print(item)

    return download_pages


def search_db(GLOBALS, shared_db_con):
    cur = shared_db_con.cursor()

    download_pages = list()
    print_list = list()
    index = 1
    sqlite_query = '''
        SELECT artist_name, album_name, popularity, is_private, download_page
        FROM album
        WHERE artist_name LIKE ? OR album_name LIKE ?
        ORDER BY popularity DESC
    '''

    download_pages.append(None)  # fix index

    search_string = GLOBALS['search']
    search_iter = ('%' + search_string + '%', '%' + search_string + '%')
    sqlite_result = cur.execute(sqlite_query, search_iter).fetchall()

    for (artist_name, album_name, popularity, is_private,
         download_page) in sqlite_result:
        download_pages.append(download_page)
        print_list.append(f'{index} - {artist_name} - {album_name} ({popularity})')
        index += 1

    for item in print_list[::-1]:
        print(item)

    return download_pages


def download_albums(download_pages, zip_directory, shared_driver, GLOBALS):
    '''Will accept a list of bandcamp download pages, iterate through them using
    the shared_driver, downloading them into the provided zip_directory and
    unzipping them into GLOBALS['directory']'''
    # TODO: zip_directory needs to be added as an argument and passed through GLOBALS
    if (not sign_in(shared_driver, GLOBALS)):
        log("ERROR", "failed to sign in!", GLOBALS)
        return False

    dl_url_xpath = "//a[@data-bind='attr: { href: downloadUrl }, visible: downloadReady() && !downloadError()']"
    zip_name_regex = r'(?<=filename\*=UTF-8\'\').+?(?=.zip)'

    download_urls = []

    for download_page in download_pages:
        shared_driver.get(download_page)
        shared_driver.implicitly_wait(5)
        download_url = None

        format_dropdown = Select(shared_driver.find_element(by=By.ID, value='format-type'))
        format_dropdown.select_by_value(GLOBALS['format'])

        while (download_url is None):
            download_element = shared_driver.find_element(by=By.XPATH,
                                                          value=dl_url_xpath)
            download_url = download_element.get_attribute("href")
            # DEBUG:
            log('INFO', f'download_url is {download_url}', GLOBALS)
            sleep(1)

        download_urls.append(download_url)

    shared_driver.quit()
    download_counter = 0

    for download_url in download_urls:
        download_counter += 1
        print(f'Downloading #{download_counter} of {len(download_urls)}...')
        if (not GLOBALS['DRY_RUN']):
            response = requests.get(download_url)

            zip_name_pre_regex = response.headers.get("Content-Disposition")
            zip_name = re.findall(zip_name_regex, zip_name_pre_regex)[0]
            zip_name = urllib.parse.unquote(zip_name)
            zip_name += '.zip'
            zip_path = os.path.join(zip_directory, zip_name)

            print(f'Downloaded {zip_name}; unzipping...')

            if not os.path.exists(zip_directory):
                os.makedirs(zip_directory)

            with open(zip_path, 'wb') as zip_file:
                zip_file.write(response.content)

            # extract artist & name out of zip string
            zip_name = zip_name[:-4]
            parts = zip_name.split(" - ")
            artist = parts[0]
            # if an zip is named something like 'dsfwan - GEO - C05.zip' then it will
            # set artist to dsfwan and album will be the rest (GEO - C05)
            album = " - ".join(parts[1:]) if len(parts) > 1 else parts[1]

            with ZipFile(zip_path, 'r') as zip_object:
                # build unzip_path
                unzip_path = os.path.join(GLOBALS['directory'], f'{artist}/{album}')
                # TODO: error handling for FileExistsError
                os.makedirs(unzip_path)
                log("TESTING", f'downloaded {download_url} to {zip_path};'
                               f' attempting to unzip into {unzip_path}',
                               GLOBALS)

                zip_object.extractall(path=unzip_path)


def log(type, message, GLOBALS):
    '''Print and record a debug message'''
    message = str(type) + ': ' + str(message)
    if (GLOBALS['DEBUG']):
        print(message)
        with open(GLOBALS['DEBUG_FILE'], "a") as debug_file:
            debug_file.write(message + '\n')


if __name__ == "__main__":
    main()
