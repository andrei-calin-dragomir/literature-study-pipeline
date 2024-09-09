import os
import argparse
import traceback
from dotenv import load_dotenv
from datetime import datetime
from paper_interpreter import PaperInterpreter
from paper_extraction.sch_wrapper import SchWrapper
from paper_extraction.dblp_parser import DBLPParser
from paper_extraction.web_scraper import WebScraper
from paper_extraction.http_requests import get_conference_rank, get_journal_rank
from database.db_manager import DatabaseManager
from database.models import Study, StudyInput, Report, CriteriaAssessment, ContentHeaders, Content, Paper, VenueRank
from utils.json_utils import validate_json
from typing import List
import csv

class StudyRunner:
    def __init__(self, study_input_path: str, dblp_path: str, openai_api_key: str, collect_content: bool=False, generate_report: bool=False):
        self.start_time = datetime.now()
        self.collect_content = collect_content
        self.generate_report = generate_report

        self.db = DatabaseManager()

        self.study = Study()
        self.study.study_date = datetime.now().date()
        self.study.dblp_used = os.path.basename(dblp_path)
        self.study.papers_collected, self.study.reports_collected = 0, 0
        self.db.session.add(self.study)
        
        self.study_input = StudyInput(
            study=self.study,
            **validate_json(study_input_path, os.path.join('schemas', 'study_input_schema.json'))
        )
        self.db.session.add(self.study_input)

        self.paper_collector = DBLPParser(dblp_path, self.study_input)
        if self.collect_content: self.web_scraper = WebScraper()
        if self.generate_report: self.interpreter = PaperInterpreter(openai_api_key)
        self.sch_api = SchWrapper()

        self.accepted_venues_set = set(self.study_input.manually_accepted_venue_codes)
        self.local_venue_rank_dict = {}
    
    # Do all filtering of papers based on initial criteria here
    # If a paper passes the criteria, it gets saved in the database
    def run(self, batch_size: int=-1):
        try:
            for paper in self.paper_collector.get_papers():
                self.add_paper_identifiers(paper)
                paper.venue_rank = self.local_venue_rank_dict.get(paper.venue_code)
                if paper.venue_rank is None: 
                    try:
                        self.add_venue_ranking_info(paper)
                    except:
                        paper.venue_rank = VenueRank.MISSING
                self.local_venue_rank_dict[paper.venue_code] = paper.venue_rank

                # Check if publishing venue of the paper is valid
                if (paper.venue_key.startswith(tuple(self.accepted_venues_set)) or self.is_valid_rank(paper.venue_rank)):
                    paper.study = self.study
                    self.db.session.add(paper)
                    print("I got paper data")

                    if self.collect_content:
                        try:
                            content, metrics = self.sch_api.add_semantic_scholar_data(paper)
                            if not content.abstract:
                                content.abstract = self.web_scraper.get_abstract(paper.publisher_source)
                            print("I got abstract")
                            self.db.session.add(content)
                            self.db.session.add(metrics)
                        except Exception as e:
                            print(f"Error in content collection: {e}")

                    if self.generate_report:
                        try:
                            report = Report(paper=paper)
                            self.db.session.add(report)

                            crit_assessment_corpora = self.format_content_sections(content, 
                                                                            [ContentHeaders.tldr, ContentHeaders.abstract])

                            criteria_assessments : List[CriteriaAssessment] = self.interpreter.get_criteria_assessments(
                                crit_assessment_corpora, list(self.study_input.inclusion_criteria))
                            
                            if criteria_assessments:
                                for ca in criteria_assessments: 
                                    ca.report = report
                                self.db.session.add_all(criteria_assessments)

                            report.research_question_assessments = None  # TODO: Add research question assessments
                            self.study.reports_collected += 1

                        except Exception as e:
                            print(f"Error in report generation: {e}")

                self.study.papers_collected += 1
                if self.study.papers_collected == batch_size: break
        finally:
            print(f"New papers found: {self.study.papers_collected}")
            self.study.total_runtime = (datetime.now() - self.start_time).total_seconds()


    def format_content_sections(self, content: Content, sections: list[ContentHeaders]=None) -> str:
        section_contents = []
        if sections: sections.sort(key=lambda x: x.value)
        else: sections = list[ContentHeaders]

        for section in sections:
            section_name = section.name.lower()
            if hasattr(content, section_name):
                section_contents.append(f"{section_name}:\n{getattr(content, section_name)}\n")

        return '\n'.join(section_contents)

    # This could be extended to gather more identifiers from other paper DBs
    def add_paper_identifiers(self, paper: Paper):
        if paper.doi is None:
            self.sch_api.get_paper_identifiers(paper)

    def add_venue_ranking_info(self, paper: Paper):
        if paper.venue_type == 'conf':
            paper.venue_rank = get_conference_rank(paper.venue_code)
        elif paper.venue_type == 'journals':
            paper.venue_rank = get_journal_rank(paper.venue_code)

    def is_valid_rank(self, rank : VenueRank) -> bool:
        if self.study_input.venue_rank_threshold is None:
            return True
        return rank.value <= VenueRank[self.study_input.venue_rank_threshold].value

    def finalize_session(self) -> int:
        # Commit the session
        try:
            self.db.session.commit()
            print('All data successfully commited.')
            self.db.session.close()
            print('Database session closed.')
            return self.study.id
        except Exception as e:
            self.db.session.rollback()
            print(traceback.format_exc())

if __name__ == "__main__":
    load_dotenv()

    try:
        parser = argparse.ArgumentParser(description="Process the study design pipeline with various options.")
        parser.add_argument('--study', type=str, help='The path to the study input to be used <json>.')
        parser.add_argument('--dblp', type=str, help='The path to the dblp to be used <xml>.')
        parser.add_argument('--batch', type=int, help='Number of papers to process in current run.')
        parser.add_argument('--collect_content', action='store_true', default=False, help='Flag to collect content using SchWrapper or WebScraper.')
        parser.add_argument('--generate_report', action='store_true', default=False, help='Flag to generate reports for papers.')
        parser.add_argument('--export_all', action='store_true', default=False, help='Export all study data into a csv file.')
        parser.add_argument('--export_summary', action='store_true', default=False, help='Export some study data into a csv file.')

        args = parser.parse_args()

        # Parse run arguments
        if not args.study or not args.dblp:
            print('For a new run, both a study as well as a dblp file need to be specified')
            exit(0)
        elif not os.path.exists(args.study):
            print(f"Study design file not found on path {args.study}")
            exit(0)
        elif not os.path.exists(args.dblp):
            print(f"Dblp file not found on path {args.dblp}")
            exit(0)

        study_run = StudyRunner(args.study, args.dblp, os.getenv('OPENAI_API_KEY'), collect_content=args.collect_content, generate_report=args.generate_report)
        
        # Run content collection and/or report generation based on flags
        study_id = study_run.run(args.batch)

        # Export data to CSV if specified
        if args.export_all:
            with open('result.csv', 'w') as f:
                out = csv.writer(f)
                out.writerow([column.name for column in Paper.__table__.columns])

                for item in study_run.db.get_study_papers(study_id):
                    out.writerow([getattr(item, column.name) for column in Paper.__table__.columns])

        study_run.finalize_session()

        # TODO
        if args.export_summary:
            pass

    except Exception as e:
        print(traceback.format_exc())