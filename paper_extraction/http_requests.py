import requests
from database.models import VenueRank
from bs4 import BeautifulSoup
import time
import functools

# Decorator that makes the function sleep for 1 second before calling
def sleep_before_call(func):
    @functools.wraps(func)  # Preserve function name and docstring
    def wrapper(*args, **kwargs):
        time.sleep(1)  # Sleep for 1 second
        return func(*args, **kwargs)
    return wrapper

@sleep_before_call
def get_conference_rank(venue_code: str) -> VenueRank:
    url_template = "https://portal.core.edu.au/conf-ranks/?search={}&by=acronym&source=CORE2023&sort=arank&page=1"
    url = url_template.format(venue_code)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')

        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:
                columns = row.find_all('td')
                acronym_found = columns[1].text.strip()
                rank = columns[3].text.strip()
                if acronym_found.lower() == venue_code.lower():
                    return VenueRank.from_string(rank)
        else:
            print(f"No rank found for conference {venue_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving conference rank: {e}")
    return VenueRank.MISSING

@sleep_before_call
def get_journal_rank(venue_title: str) -> VenueRank:
    url_template = "https://portal.core.edu.au/jnl-ranks/?search={}&by=title&source=all&sort=atitle&page=1"
    url = url_template.format('+'.join(venue_title.split()))

    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        soup = BeautifulSoup(response.content, 'html.parser')
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
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving journal rank: {e}")
    return VenueRank.MISSING
