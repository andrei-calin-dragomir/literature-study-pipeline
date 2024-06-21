import time,csv, re
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox 
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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

def append_to_file(filename, strings):
	with open(filename, 'w+') as file:
		# Move to the end of the file
		# file.seek(0, 2)
		# Append strings to the file
		for string in strings:
			file.write(string + '\n')

def get_html_source(url):
    # sleep to avoid being banned from the website
    time.sleep(3)
    driver.get(url) # go to the page
    # Waits until the word abstract appears in the page
    try:
        # wait until form shows up
        wrapper = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH,
                "//*[contains(text(), 'bstract') or contains(text(), 'summary')]"))
        )

        # print("Element is present in the DOM now")
    except TimeoutException:
        print("Element did not show up")
        return None
    return driver.page_source

def find_next_long_text(start_element):
    current = start_element.next_element

    while current:
        if isinstance(current, str) and len(current.strip()) > 100:
            # Found a text node with more than 100 characters
            return current.parent
        elif current.string and len(current.string.strip()) > 100:
            # Found an element with text content > 100 characters
            return current

        current = current.next_element

    # If no element is found, return None
    return None

def get_abstract(html_source):
	soup = BeautifulSoup(html_source, 'html.parser')
	
	# Create a case-insensitive regular expression pattern
	pattern = re.compile(re.escape('abstract'), re.IGNORECASE)
	result = soup.find(string=pattern)

	# Get the next element that has more than 100 characters
	next_element = find_next_long_text(result)
	siblings = [sibling.text for sibling in next_element.find_next_siblings()]
	
	elements = [next_element.text]
	elements.extend(siblings)

	return elements

urls = read_paper('data/papers.csv')

for url in urls:
    print(url, '\n', '\n')
    html_source = get_html_source(url[-1])
    # goes to the next paper if the abstract is not found
    if not html_source:
        continue
    abstract = get_abstract(html_source)
    for element in abstract:
        append_to_file(f'{url[0]}-{url[1]}', abstract)
