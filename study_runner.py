import os
import csv
import json
import time
from datetime import datetime
from utils.text_parsing import solve_cnf
from semanticscholar import SemanticScholar, Paper
from utils.file_io import iterate_xml, init_results_dir, init_results_file, load_json_file
from utils.text_parsing import extract_doi_from_url

STUDY_DESIGN_SCHEMA = {
  "type": "object",
  "properties": {
    "study_name": {
      "type": "string"
    },
    "research_goal": {
      "type": "string"
    },
    "research_questions": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "inclusion_criteria": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "exclusion_criteria": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "year_min": {
      "type": "integer",
      "minimum": 0
    },
    "year_max": {
      "type": "integer",
      "minimum": 0
    },
    "search_words": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "venue_codes": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "study_name",
    "research_goal",
    "research_questions",
    "inclusion_criteria",
    "exclusion_criteria",
    "year_min",
    "year_max",
    "search_words",
    "venue_codes"
  ]
}

RESULTS_HEADERS = ['id', 'title', 'year', 'authors', 'key', 'link', 'citation_count', 'influential_citation_count',
                   'abstract', 'tldr', 'is_open_access', 'pdf_link',
                   'inclusion_res', 'exclusion_res', 'inclusion_comments', 'exclusion_comments']

class StudyRunner:
    def __init__(self, study_design_path: str, dblp_path: str, output_directory_path: str, api_key: str):
        self.start_time = datetime.now()
        self.sch = SemanticScholar()

        # Store the dblp_path
        self.dblp_path = dblp_path
        self.api_key = api_key 

        self.results_directory = init_results_dir(output_directory_path)
        self.results_file = init_results_file(self.results_directory, RESULTS_HEADERS)
        self.study_design = load_json_file(study_design_path, STUDY_DESIGN_SCHEMA)
        
        
        self.summary = {'study_design': self.study_design,
                        'dblp': os.path.basename(self.dblp_path),
                        'runtime': 0}
        

    @classmethod
    def reload(cls, old_results_directory: str, api_key: str):
        instance = cls.__new__(cls)
        instance.start_time = datetime.now()
        instance.sch = SemanticScholar()
        instance.api_key = api_key
        
        # Restore all required data
        instance.results_directory = old_results_directory
        instance.results_file = os.path.join(old_results_directory, 'results.csv')

        with open(os.path.join(old_results_directory,'summary.csv'), 'r') as file:
            instance.summary = json.load(file)

        instance.study_design = instance.summary['study_design']


        return instance
    
    def _finalize(self):
        self.summary['runtime'] = str(self.summary['runtime'] + datetime.now() - self.start_time)

        summary_path = os.path.join(self.results_directory, 'summary.json')
        with open(summary_path, 'w', newline='') as file:
            json.dump(self.summary, file, indent=4)

    # This function collects papers related to the study
    def gather_papers(self, batch_size):
        index = 0
        search_query = " AND ".join(self.study_design['search_words'])
        
        with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=RESULTS_HEADERS)

            # Parse all entries in the DBLP database.
            for dblp_entry in iterate_xml(self.dblp_path):
                key = dblp_entry.get('key')
                result = {}
                try:
                    if (key.startswith(tuple(self.study_design['venue_codes'])) and
                        int(dblp_entry.find('year').text) >= int(self.study_design['year_min']) and
                        int(dblp_entry.find('year').text) <= int(self.study_design['year_max'])):
                        
                        title = ''.join(dblp_entry.find('title').itertext())
                        
                        if solve_cnf(title, search_query):
                            authors = ' & '.join(''.join(author.itertext()) for author in
                                                dblp_entry.findall('author'))
                            
                            ee = dblp_entry.find('ee')
                            if ee is not None:
                                ee = ee.text
                                
                            result.update({
                                'id': index,
                                'title': title.replace(',', ';'),
                                'year': dblp_entry.find('year').text,
                                'authors': authors,
                                'key': key,
                                'link': ee
                            })

                            if ee:
                                doi = extract_doi_from_url(ee)
                                extra_info = self.sch.get_paper(doi, 
                                                                fields=['abstract', 'citationCount', 'influentialCitationCount', 'isOpenAccess', 'openAccessPdf', 'tldr'])
                                result.update({
                                    'tldr' : extra_info.tldr['text'] if extra_info.tldr else extra_info.tldr,
                                    'abstract' : extra_info.abstract,
                                    'citation_count' : extra_info.citationCount,
                                    'influential_citation_count' : extra_info.influentialCitationCount,
                                    'is_open_access' : extra_info.isOpenAccess,
                                    'pdf_link' : extra_info.openAccessPdf
                                })
                            
                            # Write the result to the CSV file
                            writer.writerow(result)
                            index += 1
                            if index == batch_size: break

                except AttributeError as e:
                    print(e)

        self.summary['paper_collection_size'] = index
        return index