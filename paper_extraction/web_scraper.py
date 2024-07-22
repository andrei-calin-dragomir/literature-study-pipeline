import time
from bs4 import BeautifulSoup
from database.models import VenueRank
from utils.text_parsing_utils import extract_long_text, clean_text
from selenium.webdriver import Firefox 
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, InvalidArgumentException

class WebScraper:
    def __init__(self):
        # configures the browser for scraping
        firefox_options = Options()
        firefox_options.add_argument("--headless") # browser in background
        firefox_options.add_argument('--disable-blink-features=AutomationControlled')

        self.driver = Firefox(options=firefox_options)
        self.driver.set_window_size(1920, 1080)

    def get_full_page_source(self, url : str):
        current_url, page_source = "", "" 
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(15)
            time.sleep(5) 
            current_url = self.driver.current_url
            page_source = self.driver.page_source
        except InvalidArgumentException:
            print("URL Error")
        except WebDriverException:
            print("Redirection Error")
        return current_url, page_source

    def get_conference_rank(self, venue_code: str) -> VenueRank:
        url_template = "https://portal.core.edu.au/conf-ranks/?search={}&by=acronym&source=CORE2023&sort=arank&page=1"
        url = url_template.format(venue_code)

        try:
            self.driver.get(url)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table')

            if table:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    columns = row.find_all('td')
                    acronym_found = columns[1].text.strip()
                    rank = columns[3].text.strip()
                    if acronym_found.lower() == venue_code.lower():
                        # self.driver.close()
                        return VenueRank.from_string(rank)
            else:
                print(f"No rank found for conference {venue_code}")
        except Exception as e:
            print(f"Error retrieving conference rank: {e}")
        return VenueRank.MISSING

    def get_journal_rank(self, venue_title: str) -> VenueRank:
        url_template = "https://portal.core.edu.au/jnl-ranks/?search={}&by=title&source=all&sort=atitle&page=1"
        url = url_template.format('+'.join(venue_title.split()))

        try:
            self.driver.get(url)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table')

            if table:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    columns = row.find_all('td')
                    title_found = columns[0].text.strip()
                    rank = columns[3].text.strip()
                    if title_found.lower() == venue_title.lower():
                        return VenueRank.from_string(rank)
            else:
                print(f"No rank found for journal: {venue_title}")
        except Exception as e:
            print(f"Error retrieving journal rank: {e}")
        return VenueRank.MISSING

    def get_pdf_source(venue_code:str) -> str:
        pass

    def get_abstract(self, url : str) -> str:
        current_url, html_source = self.get_full_page_source(url)
        if 'sciencedirect' in current_url:
            return self._get_text_by_id(html_source, 'abstracts')
        elif 'ieee' in current_url:
            return self._get_ieee_abstract(html_source)
        elif 'arxiv' in current_url:
            return self._get_text_by_id(html_source, 'abs')
        elif ('emerald' or 'acm') in current_url:
            return self._get_text_by_id(html_source, 'abstract')
        elif 'springer' in current_url:
            return self._get_text_by_id(html_source, 'Abs1-content')

        return self._get_possible_abstract(html_source)

    def _get_possible_abstract(self, html_source):
        soup = BeautifulSoup(html_source, 'html.parser')
        abstract = "" 

        # Remove all tags not including informative content
        for script in soup(["script", "style", "ul", "li"]):
            script.decompose()

        text_chunks = extract_long_text(soup.text, 200)
        abstract = clean_text("".join(text_chunks))

        index = abstract.lower().find('abstract')
        if index != -1:
            return abstract[index:]

        return abstract

    def _get_text_by_id(self, html_source, item_id):
        soup = BeautifulSoup(html_source, 'html.parser')
        abstract = soup.find(id=item_id)
        if abstract:
            return clean_text(abstract.text) 
        return ''

    def _get_ieee_abstract(self, html_source):
        soup = BeautifulSoup(html_source, 'html.parser')
        return soup.select_one('meta[property="og:description"]')['content']
    
    def __del__(self):
        self.driver.quit()
        print("Stopped firefox driver.")