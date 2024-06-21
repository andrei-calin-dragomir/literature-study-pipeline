import time
import csv
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox 
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# read from csv file
with open('data/papers.csv') as f:
    csv_reader = csv.reader(f)

    # get link from csv
    #for row in csv_reader:
    #   print(row[0], row[-1])
    paper_url = next(csv_reader)

paper_url = paper_url[-1]
print(paper_url)

# the URL of the Perplexity website
url = "https://www.perplexity.ai/"

firefox_options = Options()
firefox_options.add_argument("--headless") # Opens the browser up in background

driver = Firefox(options=firefox_options)

## sleep to avoid being banned from the website
time.sleep(3)
driver.get(url)

try:
    # wait until form shows up
    wrapper = WebDriverWait(driver, 3).until(
      EC.presence_of_element_located((By.XPATH, "//textarea"))
    )
    print("Element is present in the DOM now")
except TimeoutException:
    print("Element did not show up")

search_box = driver.find_element("xpath", "//textarea")

question = f"Can you extract the abstract from the paper {paper_url}?"
search_box.send_keys(question)

# Submit the question
search_box.send_keys(Keys.RETURN)

# Wait for the response to load
time.sleep(5)
print(driver.page_source)

## Parse the HTML content using Beautiful Soup
#soup = BeautifulSoup(html, "html.parser")
#
### Find the form element on the page
#form = soup.find("textarea")
#
### Set the value of the input field to your question
#form.string = "What is the meaning of life?"
#
### Find the submit button
#submit_button = soup.find("button", {"aria-label": "Submit"})

## Get the URL of the submit action
#submit_url = form["action"]
#
## Prepare the form data
#form_data = {
#    input_field["name"]: input_field["value"]
#    for input_field in form.find_all("input")
#}
#
## Send a POST request to the submit URL with the form data
#response = requests.post(submit_url, data=form_data)
#
## Parse the response HTML content
#response_soup = BeautifulSoup(response.content, "html.parser")
#
## Find the element containing the answer
#answer_element = response_soup.find("div", {"class": "answer"})
#
## Print the answer
#if answer_element:
#    print(answer_element.text)
#else:
#    print("No answer found.")
