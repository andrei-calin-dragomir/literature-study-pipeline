from .web_scraper import WebScraper
from .sch_wrapper import SchWrapper
from typing import Generator, Dict, Set
from database.db_manager import DatabaseManager
from database.models import Paper, StudyInput, VenueRank
from utils.text_parsing_utils import iterate_xml, solve_cnf, extract_doi_from_url



class Factory:
    def __init__(self, dblp_path : str , study_input : StudyInput):
        # Store the dblp_path
        self.dblp_path = dblp_path
        self.study_input = study_input
        self.sch = SchWrapper()
        self.web_scraper = WebScraper()

        # store all venue ranks already found previously
        self.local_venue_rank_dict : Dict[str, VenueRank] = {}

        self.search_query = ' AND '.join(f"({' OR '.join(set(search_group))})" for search_group in list(self.study_input.search_word_groups))
        self.accepted_venues_set : Set[str] = set(self.study_input.manually_accepted_venue_codes)

    def get_papers(self) -> Generator[Paper, None, None]:        
        for dblp_entry in iterate_xml(self.dblp_path):
            key = dblp_entry.get('key')
            
            try:
                if self.is_valid_venue_type(key):
                    year = int(dblp_entry.find('year').text)
                    
                    if self.is_valid_year(year):
                        title = ''.join(dblp_entry.find('title').itertext())
                        
                        if solve_cnf(title, self.search_query):
                            paper = self.create_paper(title, year)
                            self.add_paper_identifiers(paper, dblp_entry)
                            self.add_venue_info(paper, key)
                            
                            if self.is_valid_paper(paper):
                                yield paper
            except AttributeError as e:
                print(e)

    def create_paper(self, title: str, year: int) -> Paper:
        paper = Paper()
        paper.title = title
        paper.year = year

        return paper

    def add_paper_identifiers(self, paper: Paper, dblp_entry):
        ee = dblp_entry.find('ee')
        if ee is not None:
            ee_text = ee.text
            paper.doi = extract_doi_from_url(ee_text)
            paper.publisher_source = ee_text

            if paper.doi is None:
                self.sch.get_paper_identifiers(paper)

    def add_venue_info(self, paper: Paper, key: str):
        paper.venue_type, paper.venue_code, paper.venue_key = key.split('/')
        paper.venue_rank = self.local_venue_rank_dict.get(paper.venue_code)
        
        if paper.venue_rank is None:
            if paper.venue_type == 'conf':
                paper.venue_rank = self.web_scraper.get_conference_rank(paper.venue_code)
            elif paper.venue_type == 'journals':
                paper.venue_rank = self.web_scraper.get_journal_rank(paper.venue_code)
            self.local_venue_rank_dict[paper.venue_code] = paper.venue_rank

    def is_valid_venue_type(self, key: str) -> bool:
        return key.startswith(tuple(self.study_input.accepted_venue_types))

    def is_valid_year(self, year: int) -> bool:
        return int(self.study_input.year_min) <= year <= int(self.study_input.year_max)
    
    def is_valid_rank(self, rank : VenueRank) -> bool:
            if self.study_input.venue_rank_threshold is None:
                return True
            return rank.value <= VenueRank[self.study_input.venue_rank_threshold].value

    def is_valid_paper(self, paper: Paper) -> bool:
        return (paper.venue_key.startswith(tuple(self.accepted_venues_set)) or 
                self.is_valid_rank(paper.venue_rank))
