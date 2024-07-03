import os
import csv
import time
import bs4
import requests
import time,csv, re
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox 
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidArgumentException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Opens the browser up in background
firefox_options = Options()
firefox_options.add_argument("--headless")
driver = Firefox(options=firefox_options)

def read_paper(path):
    with open(path) as f:
        csv_reader = csv.reader(f)
        urls = [next(csv_reader) for _ in range(20)]
    return urls

def get_html_source(url):
    try:
        # sleep to avoid being banned from the website
        time.sleep(3)
        driver.get(url) # go to the page
        # Waits until the word abstract appears in the page
        # wait until form shows up
        wrapper = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH,
                "//*[contains(text(), 'bstract') or contains(text(), 'summary')]"))
        )

        # print("Element is present in the DOM now")
        return driver.page_source
    except Exception as e:
        print(e)
        return None

# Function to get the first sibling with large text
def get_first_large_text_sibling(heading):
    sibling = heading.find_next_sibling()
    while sibling:
        # Check if the sibling contains large text (heuristic: checking length of text)
        if sibling.name in ['p', 'div', 'span'] and 300 > len(sibling.text.strip()) > 50:
            return sibling
        sibling = sibling.find_next_sibling()
    return None

def get_abstract(html_source):
    soup = BeautifulSoup(html_source, 'html.parser')

    # List of all heading tags
    heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    
    # Find all heading elements
    headings = []
    for tag in heading_tags:
        headings.extend(soup.find_all(tag))

    # Potential abstracts
    abstract_headings = [heading for heading in headings if 'abstract' in heading.text.lower()]
    potential_abstract_contents = []

    for heading in abstract_headings:
        print("Heading:", heading.text.strip())
        large_text_sibling = get_first_large_text_sibling(heading)
        if large_text_sibling:
            print("Found potential abstract contents.", large_text_sibling.text.strip())
            potential_abstract_contents.append(large_text_sibling.text.strip())
        else:
            print("No content found for this heading.")

    print("Using most promising (largest) abstract found...")
    return max(potential_abstract_contents, key=len, default=None)

# TODO This function can be extended to satisfy the need for accessing other parts of the paper.
def extract_abstracts_from_papers(input_csv, output_csv, total_runs, starting_point=0):
    abstracts_extracted = 0
    try:
        with open(input_csv, newline='', encoding='utf-8') as input_file, open(output_csv, 'a', newline='', encoding='utf-8') as output_file:
            csv_reader = csv.reader(input_file)
            rows = list(csv_reader)
            csv_writer = csv.DictWriter(output_file, fieldnames=['index','abstract'])

            # 1 starting index for the header
            for index, row in enumerate(rows[starting_point if starting_point > 0 else 1:total_runs], starting_point):
                link = row[-1]
                html_source = get_html_source(link)
                # goes to the next paper if the abstract is not found
                if not html_source:
                    csv_writer.writerow({'index': None})
                    continue
                abstract = get_abstract(html_source)
                if abstract:
                    csv_writer.writerow({'index': index, 
                                         'abstract': abstract})
                    abstracts_extracted += 1
            return abstracts_extracted
    except OSError or Exception as e:
        raise(f"Error during processing:{e}")

# Example usage
if __name__ == "__main__":
    html_source = get_html_source('https://doi.org/10.1109/CDC.2017.8264174')
    print(get_abstract(html_source))
