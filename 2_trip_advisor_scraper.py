import math
from time import sleep
from threading import Thread
from locators import Locators
import utils
import logging

# Set up the logger
logging.basicConfig(level=logging.INFO)

# Add a console handler for INFO messages
console_handler_info = logging.StreamHandler()
console_handler_info.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler_info)

# Add a console handler for ERROR messages
console_handler_error = logging.StreamHandler()
console_handler_error.setLevel(logging.ERROR)
logging.getLogger().addHandler(console_handler_error)

# Variables
workers = 1
records = []
csv_writer = None
total = finished = running_threads = 0
base_url = 'https://www.tripadvisor.com'
input_filepath = 'inputs/items_urls.csv'
output_filepath = 'outputs/pages.csv'

records_template = {
    'Name': '',
    'Address': '',
    'Contact': '',
    'Ranking': '',
    'Cuisine': '',
    'Reviews': '',
    'Opening_hours': '',
    'Ratings': '',
    'Website': '',
    'Item_url':''
}


def write_results_to_files(_all=False):
    """
    Writes records to the CSV file.

    Args:
        _all (bool, optional): Flag to indicate whether to write all records. Defaults to False.
    """
    global records, output_filepath, csv_writer

    try:
        # Check if there are records to write or the _all flag is set
        if len(records) > 0 or _all:
            # Initialize CSV writer for appending data
            csv_writer = utils.get_csv_writer(output_filepath, 'a')

            # Write records to the CSV file
            while len(records) > 0:
                record = records.pop(0)
                csv_writer.writerow(record)

            # Reinitialize CSV writer for further appending
            csv_writer = utils.get_csv_writer(output_filepath, 'a')

    except Exception as e:
        logging.error(f"An error occurred in the write_results_to_files function: {e}")
        raise



def manage_threads():
    """
    Main Thread Method: Manages the number of running threads and displays progress until the limit is reached.

    Updates progress and writes results to files while managing the running threads.
    """
    global workers, finished, total, running_threads

    try:
        # Keep updating progress and writing results until running threads reach the limit
        while running_threads >= workers:
            write_results_to_files()
            sleep(0.1)
            utils.write_to_console(f'Progress: {finished}/{total} | {utils.time_progress()}')

        # Final update of progress
        utils.write_to_console(f'Progress: {finished}/{total} | {utils.time_progress()}')

    except Exception as e:
        logging.error(f"An error occurred in the manage_threads function: {e}")
        raise



def start_workers(items, start, limit):
    """
    Main thread: Distributes the processing of items among multiple workers using threads.

    Args:
        items (list): List of items to be processed.
        start (int): Starting index for the items to be processed.
        limit (int): Maximum number of items each worker should process.
    """
    global workers, total, finished, running_threads

    try:
        total = len(items)

        # Iterate over workers and start a thread for each segment of items
        for worker_id in range(workers):
            end = start + limit

            # Adjust the end index to prevent exceeding the total number of items
            if end > total:
                end = total

            # Start a thread for the current segment of items, crawl through each item in targeT Function
            thread = Thread(target=crawl_records, args=(items[start:end],))
            thread.start()

            # Update running threads count and manage them
            running_threads += 1
            manage_threads()

            # Update the start index for the next worker
            start = end

        # Monitor running threads and display progress until all threads finish
        while running_threads > 0:
            write_results_to_files(_all=True)
            sleep(0.5)
            utils.write_to_console(f'Progress: {finished}/{total} | {utils.time_progress()}')

        # Final update of results and progress
        write_results_to_files(_all=True)
        utils.write_to_console(f'Progress: {finished}/{total} | {utils.time_progress()}')

    except Exception as e:
        logging.error(f"An error occurred in the Main Thread start_workers() function: {e}")
        raise


def crawl_records(urls):
    """
    Worker Thread: Crawls records for a list of URLs and extracts information using xpaths.
        - A worker extracts the relevent data for all his assigned work (Assigned Urls)
        - For all the urls: Crawl the urls and scrap the required data
        - Update Record list
    Args:
        urls (list): List of URLs to crawl and extract information.
    """
    global finished, running_threads

    try:
        # Load WebDriver for each thread
        driver = utils.load_driver()

        # Iterate over URLs to crawl and extract information
        for url in urls:
            item = records_template.copy()

            # Navigate to the URL
            driver.get(url)

            # Extract record information using xpaths
            name = utils.extract_elem_text(driver, Locators.NAME_XPATH)
            address = utils.extract_elem_text(driver, Locators.ADDRESS_XPATH)
            contact = utils.extract_elem_text(driver, Locators.CONTACT_XPATH)
            ranking = utils.extract_elem_text(driver, Locators.RANKING_XPATH)
            cuisine = utils.extract_elem_text(driver, Locators.CUISINE_XPATH)
            reviews = utils.extract_elem_text(driver, Locators.REVIEWS_XPATH)
            opening_hours = utils.extract_elem_text(driver, Locators.OPENING_HOURS_XPATH)
            website_element = utils.wait_for_elem(driver, Locators.WEBSITE_XPATH)
            website = website_element.get_attribute('href')
            ratings_element = utils.wait_for_elem(driver, Locators.RATINGS_XPATH)
            ratings = ratings_element.accessible_name.split(" ")[0].strip()

            # Assign extracted information to item dictionary
            item['Name'] = name
            item['Address'] = address
            item['Contact'] = contact
            item['Ranking'] = ranking
            item['Cuisine'] = cuisine
            item['Reviews'] = reviews
            item['Opening_hours'] = opening_hours
            item['Ratings'] = ratings
            item['Website'] = website
            item['Item_url'] = url

            # Format the record and append to the records list
            record = "+;=".join(item.values()).replace('\n', '<br>').replace('\r', '').split('+;=')
            records.append(record)

            # Update finished count
            finished += 1

        # Quit the WebDriver
        driver.quit()

        # Update running_threads count
        running_threads -= 1

    except Exception as e:
        logging.error(f"An error occurred in the crawl_records function: {e}")
        raise



def main():
    """
    Main function to execute the processing of items URLs with multiple workers.

    It initializes the CSV writer, reads item URLs from a file, and distributes the processing among workers.
        Each worker:
        1. Scrap the given url
        2. Extract the relevent details of item
        3. Store in csv
    """
    global csv_writer
    
    try:
        # Initialize CSV writer for writing headers
        csv_writer = utils.get_csv_writer(output_filepath, "w")
        csv_writer.writerow(list(records_template.keys()))

        # Initialize CSV writer for appending data
        csv_writer = utils.get_csv_writer(output_filepath, "a")
        
        # Read item URLs from the file
        with open('items_urls.csv', 'r') as file:
            urls = file.read().split('\n')[1:-1]

        total_items = len(urls)
        limit = math.ceil(total_items / workers)
        start = 0

        # Start processing with multiple workers
        start_workers(urls, start, limit)

    except Exception as e:
        logging.error(f"An error occurred during the main process: {e}")
        raise

if __name__ == "__main__":
    main()