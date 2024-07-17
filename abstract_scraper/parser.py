import re 
from bs4 import BeautifulSoup, NavigableString

class Parser:
    def __init__(self, text_length = 200):
       self.text_length = text_length 

    def extract_long_text(self, text):
        paragraphs = re.split(r'\n\n+', text)
        long_paragraphs = [
            p for p in paragraphs if len(p.split()) > self.text_length
        ]
        return long_paragraphs

    def clean_text(self, string):
        output = ''
        try:
            output = string.strip().replace('\n', '')
        except AttributeError as e:
            return ''
        return output 

    def get_abstract(self, current_url, html_source):
        abstract = ''
        print(current_url)
        if 'sciencedirect' in current_url:
            return self.get_text_by_id(html_source, 'abstracts')
        elif 'ieee' in current_url:
            return self.get_ieee_abstract(html_source)
        elif 'arxiv' in current_url:
            return self.get_text_by_id(html_source, 'abs')
        elif ('emerald' or 'acm') in current_url:
            return self.get_text_by_id(html_source, 'abstract')

        return self.get_long_text(html_source)

    def get_long_text(self, html_source):
        soup = BeautifulSoup(html_source, 'html.parser')
        abstract = "" 

        # Remove all tags not including informative content
        for script in soup(["script", "style", "ul", "li"]):
            script.decompose()

        text_chunks = self.extract_long_text(soup.text)
        abstract = self.clean_text("".join(text_chunks))

        index = abstract.lower().find('abstract')
        if index != -1:
            return abstract[index:]

        return abstract

    def get_text_by_id(self, html_source, item_id):
        soup = BeautifulSoup(html_source, 'html.parser')
        abstract = soup.find(id=item_id)
        if abstract:
            return self.clean_text(abstract.text) 
        return ''

    def get_ieee_abstract(self, html_source):
        soup = BeautifulSoup(html_source, 'html.parser')
        return soup.select_one('meta[property="og:description"]')['content']
