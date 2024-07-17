import pandas as pd
import re, logging
from file_utility import FileUtility, File
import file_utility as fu
from scraper import Scraper
from parser import Parser

def scrape(input_path, entries, abstract_length, start_entry = 0, output_path = './'):
    parser = Parser(abstract_length)

    output_file = File(
        f'{output_path}/results.csv', ['title', 'abstract', 'url']
    )
    not_found_file = File(
        f'{output_path}/not_found.csv', ['title', 'abstract', 'url']
    )

    scraped, not_found = 0, 0
    papers = FileUtility.read_papers(
        input_path, entries, start_entry = start_entry
    )

    if start_entry > len(papers):
        logger.error("invalid start entry index")

    rows = []
    for paper in papers:
        logger.info(",".join(paper))
        url = paper[-1].strip()

        # Scrape HTML using Selenium 
        scraper  = Scraper(url, abstract_length)
        current_url, html_source = scraper.get_html()

        # skips current paper if the html source cannot be retrieved 
        if html_source is None:
            not_found += 1
            continue

        abstract = parser.get_abstract(current_url, html_source)
        filename = (
                f"{paper[1]}".lstrip()
                .replace('/',"")
                .replace('.',"")
        )

        if abstract == "":
            not_found += 1
            not_found_file.add_row([paper[0], filename, abstract, url]) 
            logger.info("abstract not found")
        else:
            scraped += 1

        # index, paper name, abstract url
        output_file.add_row([paper[0], filename, abstract, url]) 

    output_file.close()
    not_found_file.close()

    logger.info(f"scraped:{scraped}, not_found: {not_found}") 

output_path = 'results'
FileUtility.make_dir(output_path)

logging.basicConfig(
    filename=f'{output_path}/abstract_scraper.log', 
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger().addHandler(logging.StreamHandler())
logger = logging.getLogger(__name__)

# scrape(input_file, entries, abstract_length, start_entry = 0, output_path = './')
scrape('./0_1544_results/not_found.csv', -1, 100, start_entry = 0, output_path = output_path)
