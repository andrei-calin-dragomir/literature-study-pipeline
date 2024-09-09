import re
from lxml import etree
from typing import Generator, List
from database.models import Paper, StudyInput

class DBLPParser:
    def __init__(self, dblp_path: str, study_input: StudyInput) -> None:
        self.dblp_file = dblp_path
        self.year_min = study_input.year_min
        self.year_max = study_input.year_max
        self.accepted_venue_types = study_input.accepted_venue_types
        self.search_query = ' AND '.join(f"({' OR '.join(set(search_group))})" for search_group in study_input.search_word_groups)

    def get_papers(self) -> Generator[Paper, None, None]:        
        for dblp_entry in self.iterate_xml():
            key = dblp_entry.get('key')
            
            if self.is_valid_venue_type(key):
                year = int(dblp_entry.find('year').text)
                
                if self.is_valid_year(year):
                    title = ''.join(dblp_entry.find('title').itertext())
                    
                    if self.solve_cnf(title, self.search_query):
                        paper = Paper()
                        paper.title = title
                        paper.year = year
                        paper.venue_type, paper.venue_code, paper.venue_key = key.split('/')

                        ee = dblp_entry.find('ee')
                        if ee is not None:
                            ee_text = ee.text
                            paper.doi = self.extract_doi_from_url(ee_text)
                            paper.publisher_source = ee_text
                        yield paper

    def is_valid_venue_type(self, key: str) -> bool:
        return key.startswith(tuple(self.accepted_venue_types))

    def is_valid_year(self, year: int) -> bool:
        return int(self.year_min) <= year <= int(self.year_max)

    # Iterate over a large-sized xml file without the need to store it in memory in
    # full. Yields every next element. Source:
    # https://stackoverflow.com/questions/9856163/using-lxml-and-iterparse-to-parse-a-big-1gb-xml-file
    def iterate_xml(self):
        doc = etree.iterparse(self.dblp_file, events=('start', 'end'), load_dtd=True)
        _, root = next(doc)
        start_tag = None

        for event, element in doc:
            if event == 'start' and start_tag is None:
                start_tag = element.tag
            if event == 'end' and element.tag == start_tag:
                yield element
                start_tag = None
                root.clear()

    @staticmethod
    def solve_or(test_string: str, boolean_expression: str):
        # Solves Atomic Disjunctions
        # the boolean expression should be written as a combination of
        # literals separated by the or operator written as 'or'
        literals = re.split("or", boolean_expression, flags=re.IGNORECASE)
        return any(
            literal.strip().lower() in test_string.lower() for literal in literals
        )

    @staticmethod
    def solve_and(test_string: str, boolean_expression: str):
        # Solves Atomic Conjunctions
        # the boolean expression should be written as a combination of
        # literals separated by the and operator written as 'and'
        literals = re.split("and", boolean_expression, flags=re.IGNORECASE)
        return all(
            literal.strip().lower() in test_string.lower() for literal in literals
        )

    def solve_cnf(self, test_string: str, boolean_expression: str):
        """
        Function that solves boolean expressions in Conjunctive Normal Form (CNF)
        """
        # solve first literals within the parenthesis
        nested_literals = self.get_text_inside_parens(boolean_expression)
        # literals in parentheses are disjunctions
        # check if all the disjunction are true
        if all(self.solve_or(test_string, x) for x in nested_literals):
            for x in nested_literals:
                boolean_expression = boolean_expression.replace(f'({x})', '')
            return self.solve_and(test_string, boolean_expression)
        return False
    
    @staticmethod
    def get_text_inside_parens(text: str) -> list:
        """
        Function that extracts the text within parentheses from a string
        @return: a list in which the elements correspond to the text
        previously in parentheses
        """
        matches = re.findall(r'\(([^)]+)\)', text)
        return list(map(str.strip, matches))

    @staticmethod
    def extract_doi_from_url(url):
        # Regular expression to match the DOI pattern
        doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
        match = re.search(doi_pattern, url, re.IGNORECASE)
        if match:
            return match.group(0)
        else:
            return None