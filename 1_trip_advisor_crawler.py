import utils
from locators import Locators
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
links = []
csv_writer = None
finished = 0
output_filepath = 'items_urls.csv'
base_url = 'https://www.tripadvisor.com'
search_query = ' Restaurants in New York, USA'
records_template = {
    'URL': '',
}



def crawl_page(driver, output_filepath=output_filepath):
    """
    Crawls the given page using the provided WebDriver for page links and writes page links to a CSV file.

    Args:
        driver: WebDriver instance for interacting with the web page.
        output_filepath: Path to the CSV file for writing page links.
    
    Returns:
        None; 
    """
    global links, csv_writer, finished

    try:
        page_items_links_elems = utils.wait_for_elems(driver, Locators.PAGE_IETM_LINK_XPATH)
        utils.wait_with_screenshot(1, driver)

        # Extract item link of single page using href of an element and store in an array
        page_links = []
        for elem in page_items_links_elems:
            page_links.append(elem.get_attribute('href'))
            finished += 1

        # Write links of a single page from array to csv file
        for page_link in page_links:
            csv_writer.writerow([page_link])

        csv_writer = utils.get_csv_writer(output_filepath, "a")

    except Exception as e:
        logging.error(f"An error occurred while crawling the page: {e}")
        raise


def main():
    """
    Main function to execute the web crawling process. It will:
        1. Open base URL
        2. Enters search query and submit
        3. Call crawl_method() for each item in the list to get item's url
        4. Goto Next page
        

    It initializes the CSV writer, loads the WebDriver, performs a search, and iteratively crawls through pages.
    """
    global csv_writer, finished

    # Initialize CSV writer for writing headers
    csv_writer = utils.get_csv_writer(output_filepath, "w")
    csv_writer.writerow(list(records_template.keys()))

    # Initialize CSV writer for appending data
    csv_writer = utils.get_csv_writer(output_filepath, "a")

    # Load WebDriver and perform initial actions
    driver = utils.load_driver()
    driver.maximize_window()

    logging.info(f"Bot activated...")
    driver.get(base_url)
    
    logging.info(f"Crawling for this search filter: {search_query} ...")
    utils.send_keys_to_elem(driver, Locators.SEARCH_FIELD_XPATH, search_query)
    utils.wait_with_screenshot(2, driver)
    submit_elem = utils.wait_for_elem(driver, Locators.SEARCH_FIELD_XPATH)
    submit_elem.submit()
    utils.wait_with_screenshot(3, driver)

    try:
        logging.info(f"Crawler started...")
        # Process multiple pages
        while True:
            # For every page
            crawl_page(driver)

            elem = utils.wait_for_elem(driver, Locators.NEXT_PAGE_BUTTON_XPATH)
            utils.wait_with_screenshot(1, driver)
            utils.write_to_console(f'Items Crawled: {finished} | {utils.time_progress()}')

            if not elem:
                break
            else:
                # Click next page button
                elem.click()
                utils.wait_with_screenshot(2, driver)
        utils.write_to_console(f'Items Crawled: {finished} | {utils.time_progress()}')

    except Exception as e:
        logging.error(f"An error occurred during the main process: {e}")
        raise

if __name__ == "__main__":
    main()