import csv
import io
import json
import os
import random
import string
import sys
import unicodedata
from datetime import datetime
from glob import glob
from pathlib import Path
from time import sleep, time

# import requests
# import requests.auth
# from lxml import html, etree
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

# Global Variables
start_time = time()

screenshots_dir_path = 'screenshots'


# General Configurations
# requests.packages.urllib3.disable_warnings()


# Utility Functions

def wait_with_screenshot(seconds, driver):
    for i in range(seconds):
        sleep(1)
        driver.save_screenshot('live.png')  # For debugging

def get_writer(file_name, _mode='w', _encoding='utf-8'):
    """This function returns an object of the file in the specified mode.

    Args:
        file_name (str): The name of the file
        _mode (char): The mode in which you want to open the file, writing is the default mode
        _encoding (str): The file encoding, default value is UTF-8

    Raises:
        FileNotFoundError: If filename is not valid
        ValueError: If mode is not valid
        LookupError: If encoding is not correct

    Returns:
        File (object): The object of the file to write
    """
    return io.open(file_name, mode=_mode, encoding=_encoding)


def get_csv_writer(file_name, _mode='w', _encoding='utf-8', _delimiter=','):
    """This function returns an object of the CSV file in the specified mode.

        Args:
            file_name (str): The name of the file
            _mode (char): The mode in which you want to open the file, writing is the default mode
            _encoding (str): The file encoding, default value is UTF-8
            _delimiter (char): Default is comma in most of the cases, rarely a pipe symbol |

        Raises:
            FileNotFoundError: If filename is not valid
            ValueError: If mode is not valid
            LookupError: If encoding is not correct

        Returns:
            File (object): The object of the CSV file to write
    """
    writer = csv.writer(open(file_name, mode=_mode, encoding=_encoding, errors='ignore'),
                        delimiter=_delimiter,
                        lineterminator='\n')

    return writer


def read_csv_as_list(file_name):
    items = []

    reader = csv.reader(open(file_name, 'r', errors='ignore', encoding='utf-8'), delimiter=',',
                        lineterminator='\n')
    header = next(reader)

    for row in reader:
        items.append(row)

    return items, header


def read_csv_as_dict(file_name, key_index=0, value_index=999):
    items = {}

    reader = csv.reader(open(file_name, 'r', errors='ignore', encoding='utf-8'), delimiter=',',
                        lineterminator='\n')
    header = next(reader)

    for row in reader:
        card_id = row[key_index]

        if value_index == 999:
            items[card_id] = row
        elif row[value_index]:
            items[card_id] = row[value_index]

    try:
        items['']
    except KeyError:
        pass

    return items, header


def read_file_as_tree(file_path):

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f'UnicodeDecodeError: File "{file_path}" is causing issues.')
            return False

        if 'ö' not in content:
            with open(file_path, 'r', encoding='cp1252', errors='ignore') as f:
                content = f.read()

        try:
            return html.fromstring(content)
        except etree.ParserError:
            print(f'Parser Error: File "{file_path}" is empty.')
            return False
    else:
        return False


def write_to_console(text):
    """This function writes provided text on the same line of the console, kind of progress bar.

        Args:
            text (str): The text that you want to display on the console.
    """
    sys.stdout.write(f'\r{text}')
    sys.stdout.flush()


def time_progress():
    """This function calculates the running time of the script.

        Returns:
            Time (str): It returns the calculated time in a formatted way to display on console.
    """
    end = time()

    hours, rem = divmod(end - start_time, 3600)
    minutes, seconds = divmod(rem, 60)

    return '{:0>2}:{:0>2}:{:05.2f}'.format(int(hours), int(minutes), seconds)


def get_tag_text(tree, xpath, _separator=''):
    """This function extracts all the text from a tree like structured element.

    Args:
        tree (elem): A tree like structure
        xpath (str): The xpath of the element that needs to be extracted
        _separator (str): The char or string that will separate multiple elements

    Returns:
        plain_text (str): The plain readable text
    """
    content = ''

    results = tree.xpath(xpath)

    for result in results:
        content += str(result).strip()

        if _separator:
            content += _separator
        else:
            return cleanup_text(content)

    if _separator and _separator in content:
        content = content[0:-len(_separator)]

    return cleanup_text(content)


def cleanup_text(text):
    """This function removes any extra line spaces and characters from the provided text.

    Args:
        text (str): The plain text that needs to be cleaned

    Returns:
        new_text (str): The cleaned text
    """
    new_text = text

    while True:

        if '\r' in new_text:
            new_text = new_text.replace('\r', '').strip()

        if '\t' in new_text:
            new_text = new_text.replace('\t', ' ').strip()

        if '\n' in new_text:
            new_text = new_text.replace('\n', ' ').strip()

        if '  ' in new_text:
            new_text = new_text.replace('  ', ' ').strip()

        if '\n' not in new_text and '  ' not in new_text:
            return new_text


def save_file_locally(file_path, content, _mode='wb'):
    """This function stores the provided content in a local file.

    Args:
        file_path (str): The relative path of the file where it needs to be stored
        content: The contents of the file
        _mode (str): The mode of the file in which to write the file.
    """

    with open(file_path, mode=_mode, encoding="utf-8") as f:
        f.write(content)


def create_files_dir(files_dir):
    """This function makes sure that the provided file path exists.

    Args:
        files_dir (str): The relative path of the directory that needs to be created recursively.

    Raises:
        FileExistsError: If the provided file path already exists.
    """

    if not os.path.isdir(files_dir):

        try:
            os.makedirs(files_dir)
        except FileExistsError:
            pass


def remove_dir_if_empty(dir_name):
    """This function makes sure that the provided file path is removed from the file storage.

    Args:
        dir_name (str): The relative path of the directory that needs to be removed.

    Raises:
        FileNotFoundError: If the file count is zero in the provided file path.

    Returns:
        Status (bool): True if file path does not exist on the file storage, Otherwise False
    """

    if os.path.isdir(dir_name):
        try:
            dirs = os.listdir(dir_name)
        except FileNotFoundError:
            dirs = []

        if len(dirs) == 0:
            os.rmdir(dir_name)
            return True
        else:
            return False

    return True


# Below are the Functions related to the Backend that use Requests module.


def get_request(page_url, _content='html', _retries=5, _verify=True, _timeout=15):

    while True:

        try:
            response = requests.get(page_url, verify=_verify, timeout=_timeout)

            if response.status_code == 200:

                if _content.lower() == 'tree':
                    return html.fromstring(response.content)
                elif _content.lower() == 'json':
                    return json.loads(response.content)
                else:
                    return response.content

            elif response.status_code == 404:
                return False
            else:
                raise Exception

        except Exception as e:

            if '[Errno 11001] getaddrinfo failed' in str(e):
                write_to_console('Internet Connection Error! Retrying...')
            else:
                _retries -= 1

            if _retries == 0:
                raise AssertionError(f'Unable to fetch response from URL: {page_url}')

            sleep(0.5)


def download_page(page_url, filepath):

    if not os.path.isfile(filepath):
        content = get_request(page_url)
        save_file_locally(filepath, content)


def get_page_tree(driver, _sleep=1):
    sleep(_sleep)
    return html.fromstring(driver.page_source)


def get_file(file_url, file_path, retries=2):

    while True:

        try:
            response = requests.get(file_url, timeout=30)

            if response.status_code == 200:
                with open(file_path, mode='wb') as f:
                    f.write(response.content)
                return True
            elif response.status_code == 404:
                return False
            else:
                raise Exception

        except Exception as e:

            if '[Errno 11001] getaddrinfo failed' in str(e):
                write_to_console('Internet Connection Error! Retrying...')
            else:
                retries -= 1

            if retries == 0:
                return False

            sleep(0.5)


def get_recursive_filepaths(directory):
    """
    This function will generate the file names in a directory
    tree by walking the tree either top-down or bottom-up. For each
    directory in the tree rooted at directory top (including top itself),
    it yields a 3-tuple (dirpath, dirnames, filenames).
    """
    file_paths = []

    for root, directories, files in os.walk(directory):

        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    return file_paths


def get_filepaths(directory, _extension='html', _depth=1):
    directory = directory.replace('./', '').strip('/')
    directory_depth = '/*' * _depth

    if ':/' not in directory:
        directory_path_pattern = f'./{directory}{directory_depth}.{_extension}'
    else:
        directory_path_pattern = f'{directory}{directory_depth}.{_extension}'

    filepaths = glob(directory_path_pattern)

    print(f'Fetching Files | Count: {len(filepaths)} | Dir: {directory_path_pattern}')

    return filepaths


def generate_card_ids(starting_id, ending_id):
    return {str(card_id): '' for card_id in range(starting_id, ending_id + 1)}


def remove_existing_files(card_ids, dir_pattern):
    scraped_card_ids = glob(dir_pattern)

    for file_path in scraped_card_ids:
        card_id = Path(file_path).stem

        try:
            del card_ids[card_id]
        except KeyError:
            pass


# Below are the Selenium Browser utils.


def load_driver(headless=False, proxy=""):
    """This function opens a Chrome browser after some configurations and returns chrome driver object.

    Args:
        headless (bool): True to run the Chrome browser in the foreground otherwise it will run in background.
        proxy (str): Proxy string to hide your real ip address from the world.

    Returns:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
    """
    options = Options()

    # options.add_argument(r"--user-data-dir=/Users/apple/Library/Application Support/Google/Chrome/Default")
    # options.add_argument(r'--profile-directory=/Users/apple/Library/Application Support/Google/Chrome/Default')

    options.page_load_strategy = "normal"        # normal, eager, none

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument(r'--user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Default')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    if headless:
        options.add_argument("--headless")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    chrome_driver_path = r'C:\chromedriver\chromedriver.exe'  # Replace with your actual path

    driver = webdriver.Chrome(options=options)

    return driver


# Following are the Functions to interact with multiple elements.


def wait_for_elems(driver, elems_xpath, _wait_in_secs=10):
    """This function wait until the presence of the specified elements is located on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elems_xpath (str): The xpath of the elements that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        WebDriverElement (list): if it is found successfully, Otherwise False
    """
    try:
        return WebDriverWait(driver, _wait_in_secs).until(
                    EC.presence_of_all_elements_located((
                        By.XPATH, elems_xpath)))
    except exceptions.TimeoutException:
        return False


def wait_for_elems_by_text(driver, elem_text, _elem_index=0, _wait_in_secs=10, _sleep=0.2):
    """This function wait until the presence of the specified elements is located on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_text (str): The visible text of the element that you want to look for.
        _elem_index (int): In case of multiple elements, you can specify index of the element to interact with.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.

    Returns:
        WebDriverElement (list): if it is found successfully, Otherwise False
    """
    elems_by_having_text_xpath = f'.//*[contains(text(), "{elem_text}")]'

    elems = wait_for_elems(driver, elems_by_having_text_xpath, _wait_in_secs)

    if len(elems) > 1 and _elem_index == 0:
        elems_by_exact_text_xpath = f'.//*[text()="{elem_text}"]'

        exact_elems = wait_for_elems(driver, elems_by_exact_text_xpath)

        if len(exact_elems) == 1:
            elems = exact_elems

    if _elem_index >= len(elems):
        return False

    return elems


def locate_elems(driver, elems_xpath, _wait_in_secs=10):
    """This function wait until the specified elements becomes visible on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elems_xpath (str): The xpath of the elements that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        WebDriverElement (list): if it is found successfully, Otherwise False
    """
    try:
        return WebDriverWait(driver, _wait_in_secs).until(
            EC.visibility_of_all_elements_located((
                By.XPATH, elems_xpath)))
    except exceptions.TimeoutException:
        return []


def locate_elems_by_text(driver, elems_text, _elem_index=0, _wait_in_secs=10):
    """This function wait until the specified elements becomes visible having specified text on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elems_text (str): The visible text of the elements that you want to look for.
        _elem_index (int): In case of multiple elements, you can specify index of the element to interact with.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        WebDriverElement (list): if it is found successfully, Otherwise False
    """
    elems_by_having_text_xpath = f'.//*[contains(text(), "{elems_text}")]'

    elems = locate_elems(driver, elems_by_having_text_xpath, _wait_in_secs)

    if len(elems) > 1 and _elem_index == 0:
        elems_by_exact_text_xpath = f'.//*[text()="{elems_text}"]'

        exact_elems = locate_elems(driver, elems_by_exact_text_xpath, _wait_in_secs)

        if len(exact_elems) == 1:
            elems = exact_elems

    if _elem_index >= len(elems):
        return []

    return elems


# Following are the Functions to interact with single elements.


def wait_until_text_present(driver, elem_xpath, elem_text, _wait_in_secs=10):
    """This function wait until the specified element becomes visible on the Web Page and also contains specified text.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        elem_text (str): The visible text of the element that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        element (WebDriverElement): if it is found successfully, Otherwise False
    """
    try:
        return WebDriverWait(driver, _wait_in_secs).until(
                    EC.text_to_be_present_in_element((
                        By.XPATH, elem_xpath), elem_text))
    except exceptions.TimeoutException:
        return False


def wait_for_elem(driver, elem_xpath, _wait_in_secs=10):
    """This function wait until the presence of the specified element is located on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        element (WebDriverElement): if it is found successfully, Otherwise False
    """
    try:
        return WebDriverWait(driver, _wait_in_secs).until(
                    EC.presence_of_element_located((
                        By.XPATH, elem_xpath)))
    except exceptions.TimeoutException:
        return False


def locate_elem(driver, elem_xpath, _wait_in_secs=10):
    """This function wait until the specified element becomes visible on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        element (WebDriverElement): if it is found successfully, Otherwise False
    """
    try:
        return WebDriverWait(driver, _wait_in_secs).until(
            EC.visibility_of_element_located((
                By.XPATH, elem_xpath)))
    except exceptions.TimeoutException:
        return False


def locate_elem_by_text(driver, elem_text, _elem_index=0, _wait_in_secs=10):
    """This function wait until the specified element becomes visible on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_text (str): The visible text of the element that you want to look for.
        _elem_index (int): In case of multiple elements, you can specify index of the element to interact with.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Raises:
        IndexError: If specified index does not exist in the list.

    Returns:
        element (WebDriverElement): It returns the specific element from the list.
    """
    elems = locate_elems_by_text(driver, elem_text, _elem_index=_elem_index, _wait_in_secs=10)

    return elems[_elem_index]


def clickable_elem(driver, elem_xpath, _wait_in_secs=10):
    """This function wait until the specified element becomes clickable on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.

    Returns:
        element (WebDriverElement): if it is found successfully, Otherwise False
    """
    try:
        return WebDriverWait(driver, _wait_in_secs).until(
                    EC.element_to_be_clickable((
                        By.XPATH, elem_xpath)))
    except exceptions.TimeoutException:
        return False


def click_elem(driver, elem_xpath, _wait_in_secs=10, _sleep=0.2):
    """This function clicks on the specified element after it becomes clickable on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.
    """
    elem_to_click = clickable_elem(driver, elem_xpath, _wait_in_secs)

    elem_to_click.click()

    sleep(_sleep)


def click_elem_by_text(driver, elem_text, _elem_index=0, _wait_in_secs=10, _sleep=0.2):
    """This function clicks on the element having specified text after the element is located on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_text (str): The visible text of the element that you want to look for.
        _elem_index (int): In case of multiple elements, you can specify index of the element to interact with.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.
    """
    elems = locate_elems_by_text(driver, elem_text, _wait_in_secs)

    driver.execute_script("arguments[0].click();", elems[_elem_index])

    sleep(_sleep)


def extract_elem_text(driver, elem_xpath, _wait_in_secs=5):
    elem = wait_for_elem(driver, elem_xpath, _wait_in_secs=_wait_in_secs)

    if elem:
        return str(elem.text).strip()
    else:
        return ''


def send_keys_to_elem(driver, elem_xpath, keys, _clear=True, _wait_in_secs=10, _sleep=0.2):
    """This function writes specified text in the field once that field is located on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        keys (str): The plain text to write in the field.
        _clear (bool): If True then clears the field before writing new text, Otherwise just append the text.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.
    """
    elem_to_send_keys_to = locate_elem(driver, elem_xpath, _wait_in_secs)

    if _clear:
        elem_to_send_keys_to.clear()
    # elem_to_send_keys_to.send_keys(keys)
    ActionChains(driver).send_keys_to_element(elem_to_send_keys_to, keys).perform()
    sleep(_sleep)


def send_keys_to_elem_by_text(driver, elem_text, keys, _clear=True, _wait_in_secs=10, _sleep=0.2):
    """This function writes specified text in the field once that field is located having specified text on the Web Page.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_text (str): The visible text of the element that you want to look for.
        keys (str): The plain text to write in the field.
        _clear (bool): If True then clears the field before writing new text, Otherwise just append the text.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.
    """
    elem_to_send_keys_to = locate_elem_by_text(driver, elem_text, _wait_in_secs)

    if _clear:
        elem_to_send_keys_to.clear()

    elem_to_send_keys_to.send_keys(keys)

    sleep(_sleep)


# Following are the Functions to perform certain actions on the Frontend using driver.


def save_browser_page_locally(driver, file_path, _sleep=0.25):
    sleep(_sleep)
    page_content = driver.page_source

    writer = get_writer(file_path)
    writer.write(page_content)
    writer.close()


def select_dropdown_value_by_text(driver, elem_xpath, dropdown_text):
    """This function selects one of the option from the given dropdown list via visible text of the option.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_xpath (str): The xpath of the element that you want to look for.
        dropdown_text (str): The text of the one of the options from the dropdown list.
    """
    elem = locate_elem(driver, elem_xpath)
    select = Select(elem)
    select.select_by_visible_text(dropdown_text)


def wait_until_url_contains_text(driver, elem_text, _wait_in_secs=10, _sleep=0.5):
    """This function wait until the current URL does not contain the specified text.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        elem_text (str): The visible text of the element that you want to look for.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.

    Returns:
        status (bool): If the URL contains the specified text then True, Otherwise False.
    """
    try:
        WebDriverWait(driver, _wait_in_secs).until(
            EC.url_contains(elem_text))
        sleep(_sleep)
        return True
    except exceptions.TimeoutException:
        return False


def switch_to_iframe(driver, _iframe_xpath='.//iframe', _wait_in_secs=10, _sleep=0.5):
    """This function switches focus of the Chrome driver to the specified iframe.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        _iframe_xpath (str): The xpath of the iframe that you want to switch to.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.

    Returns:
        status (bool): If the focus switched to the specified iframe then True, Otherwise if iframe not exists then False.
    """
    iframe = wait_for_elem(driver, _iframe_xpath, _wait_in_secs)

    if iframe:
        driver.switch_to.frame(iframe)
        sleep(_sleep)
        return True

    return False


def switch_to_iframes_within_iframes_until_exists(driver, _wait_in_secs=5, _sleep=0.5):
    """This function wait until the current URL does not contain the specified text.

    Args:
        driver (WebDriver): The Chrome driver object to handle the Chrome browser.
        _wait_in_secs (int): WebDriver waits for specified number of seconds while looking for the element.
        _sleep (float): The time for which WebDriver waits after performing the action
                        so the page could be loaded successfully and for the smooth experience with WebDriver.

    Returns:
        status (bool): If the URL contains the specified text then True, Otherwise False.
    """
    while switch_to_iframe(driver, _wait_in_secs=_wait_in_secs, _sleep=_sleep):
        pass


def scroll_down_to_bottom_of_page(driver, _pause_in_scroll=1):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        sleep(_pause_in_scroll)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break

        last_height = new_height


def scroll_to_elem(driver, elem_xpath, _wait_in_secs=10, _pause_in_scroll=1):
    elem = wait_for_elem(driver, elem_xpath, _wait_in_secs=_wait_in_secs)

    if elem:
        driver.execute_script('arguments[0].scrollIntoView();', elem)

        sleep(_wait_in_secs)

        return elem
    else:
        return False


def take_screenshot(driver):
    create_files_dir(screenshots_dir_path)

    filename_as_timestamp = datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')
    screenshot_filepath = f'{screenshots_dir_path}/{filename_as_timestamp}.png'
    driver.save_screenshot(screenshot_filepath)
    return screenshot_filepath
