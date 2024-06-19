import bs4
import csv
import requests
import time

# read from csv file
with open('results/related.csv') as f:
    csv_reader = csv.reader(f)

    # get link from csv
    #for row in csv_reader:
    #    print(row[0], row[-1])
    link = next(csv_reader)

# fetch the page content 
start = time.time()
response = requests.get(link[-1])
end = time.time()

html_content = response.content
time.sleep(5) # sleep to avoid request overload

print('request lasted:', end-start)

soup = bs4.BeautifulSoup(html_content, "html.parser") # parse the content
target_element = soup.find(string="Abstract") # find the element containing the abstract



