import csv
import io
import json
import os
import random
import string
import sys
from datetime import datetime
from time import sleep, time
import logging

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
    """
    Waits for the specified number of seconds, saving a screenshot every second.

    Args:
        seconds (int): Number of seconds to wait.
        driver: WebDriver instance for capturing the screenshot.
    """
    try:
        # Loop through the specified number of seconds
        for i in range(seconds):
            sleep(1)
            driver.save_screenshot('live.png')  # For debugging

    except Exception as e:
        logging.error(f"An error occurred in the wait_with_screenshot function: {e}")
        raise
    

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


# Following are the Functions to perform certain actions on the Frontend using driver.

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
