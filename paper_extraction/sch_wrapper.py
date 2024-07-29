import time
import requests
import functools
from typing import List, Tuple, Optional
from semanticscholar import SemanticScholar
from utils.json_utils import load_json_from_string
from database.models import Paper, Content, Metrics

# Enforce at least 1 second delay for semantic scholar API calls: https://www.semanticscholar.org/product/api
def delay_api_call(seconds):
    def decorator_delay(func):
        @functools.wraps(func)
        def wrapper_delay(*args, **kwargs):
            # print(f"Delaying for {seconds} seconds before calling {func.__name__}")
            time.sleep(seconds)
            return func(*args, **kwargs)
        return wrapper_delay
    return decorator_delay

class SchWrapper:
    def __init__(self):
        self.sch = SemanticScholar()

    @delay_api_call(1)
    def add_semantic_scholar_data(self, paper_entry: Paper) -> Tuple[Content, Metrics]:  
        data = self.sch.get_paper(paper_entry.semantic_scholar_id if paper_entry.semantic_scholar_id else paper_entry.doi, 
                fields=['isOpenAccess', 'openAccessPdf', 
                        'citationCount', 'influentialCitationCount',
                        'abstract', 'tldr'])

        if data['isOpenAccess'] == True and data['openAccessPdf']:
            paper_entry.pdf_source = data['openAccessPdf']['url']

        content = Content(
            paper = paper_entry,
            tldr = data.tldr['text'] if data.tldr else None,
            abstract = data.abstract if data.abstract else None
        )

        metrics = Metrics(
            paper = paper_entry,
            citations = data.citationCount,
            influential_citations = data.influentialCitationCount
        )

        return content, metrics
    
    # TODO Could be extended for each api we want to use to enrich the paper entries
    @delay_api_call(1)
    def get_paper_identifiers(self, paper_entry: Paper):
        paper_entry.semantic_scholar_id = self.get_semantic_scholar_id(paper_entry.title)
        if paper_entry.semantic_scholar_id:
            paper_entry.doi = self.sch.get_paper(paper_entry.semantic_scholar_id , fields=['externalIds']).externalIds.get('DOI')

    @staticmethod
    # TODO https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper_citations
    def get_semantic_scholar_citations(paper_id:str) -> List[str]:
        pass

    @staticmethod
    def get_semantic_scholar_id(paper_title: str) -> str | None:
        # URL template with a placeholder for the acronym
        url_template = "https://api.semanticscholar.org/graph/v1/paper/search/match?query="
        # Format the URL with the provided acronym
        url = url_template + paper_title

        # Make a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response content
            data = load_json_from_string(response.content)
            return data['data'][0]['paperId']
