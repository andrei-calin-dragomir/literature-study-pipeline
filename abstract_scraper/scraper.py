import time
from selenium.webdriver import Firefox 
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import WebDriverException 
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import JavascriptException 

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class Scraper:
    def __init__(self, url, abstract_length = 200):
        # configures the browser for scraping
        firefox_options = Options()
        firefox_options.add_argument("--headless") # browser in background
        firefox_options.add_argument('--disable-blink-features=AutomationControlled')

        self.driver = Firefox(options=firefox_options)
        self.driver.set_window_size(1920, 1080)
        self.abstract_length = abstract_length
        self.url = url

    def get_html(self):
        current_url, page_source = "", "" 
        try:
            self.driver.get(self.url)
            self.driver.implicitly_wait(15)
            time.sleep(5) 
            current_url = self.driver.current_url
            page_source = self.driver.page_source
        except InvalidArgumentException:
            print("URL Error")
        except WebDriverException:
            print("Redirection Error")

        self.driver.quit()
        return current_url, page_source
