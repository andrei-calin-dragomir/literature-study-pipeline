import aspose.pdf as apdf
import re
import csv

SECTION_HEADERS = ['Title', 'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'References']

class ContentPackager:
    def __init__(self, unique_id: str, pdf_path: str):
        self.unique_id = unique_id
        self.document = apdf.Document(pdf_path)
        self.index_map = self._create_index_map()
            
    def _create_index_map(self) -> dict:
        """
        Create an index map of section titles to their respective starting positions in the PDF.
        """
        index_map = {}
        titles = SECTION_HEADERS
        for i, page in enumerate(self.document.pages):
            text = page.extract_text()
            for title in titles:
                if title in text:
                    index_map[title] = i
        return index_map

    def get_section_content(self, title: str) -> str:
        """
        Get the content of a given section by its title.
        
        :param title: The title of the section.
        :return: The content of the section.
        """
        if title not in self.index_map:
            return ""
        
        start_page = self.index_map[title]
        end_page = len(self.document.pages) - 1
        
        titles = list(self.index_map.keys())
        current_title_index = titles.index(title)
        
        if current_title_index < len(titles) - 1:
            next_title = titles[current_title_index + 1]
            end_page = self.index_map[next_title] - 1
        
        section_content = ""
        for page_num in range(start_page, end_page + 1):
            section_content += self.document.pages[page_num].extract_text()
        
        return section_content.strip()
