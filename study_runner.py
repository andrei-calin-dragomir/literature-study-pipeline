import os
import argparse
import traceback
from dotenv import load_dotenv
from datetime import datetime
from paper_interpreter import PaperInterpreter
from paper_extraction.factory import Factory
from paper_extraction.sch_wrapper import SchWrapper
from database.db_manager import DatabaseManager
from database.models import Study, StudyInput, Report, CriteriaAssessment, CriteriaType, ContentHeaders, Content
from utils.json_utils import validate_json
from typing import List

class StudyRunner:
    def __init__(self, study_input_path: str, dblp_path: str, openai_api_key: str):
        self.start_time = datetime.now()

        self.db = DatabaseManager()
        self.interpreter = PaperInterpreter(openai_api_key)

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

        self.paper_collector = Factory(dblp_path, self.study_input)
    
    # Do all filtering of papers based on initial criteria here
    # If a paper passes the criteria, it gets saved in the database
    def run(self, batch_size: int=-1):
        try:
            for paper in self.paper_collector.get_papers():

                paper.study = self.study
                self.db.session.add(paper)
                try:
                    content, metrics = self.paper_collector.sch.add_semantic_scholar_data(paper)
                    if not content.abstract: content.abstract = self.paper_collector.web_scraper.get_abstract(paper.publisher_source)

                    self.db.session.add(content)
                    self.db.session.add(metrics)

                    # Start the report on the paper
                    report = Report(paper = paper)
                    self.db.session.add(report)

                    # Extract inclusion/exclusion criteria assessments
                    crit_assessment_corpora = self.format_content_sections(content, 
                                                                        [ContentHeaders.tldr, ContentHeaders.abstract])
                    
                    criteria_assessments : List[CriteriaAssessment] = self.interpreter.get_criteria_assessments(crit_assessment_corpora, 
                                                                                                                list(self.study_input.inclusion_criteria), 
                                                                                                                list(self.study_input.exclusion_criteria)
                                                                                                                )
                    if criteria_assessments:
                        for ca in criteria_assessments: ca.report = report
                        self.db.session.add_all(criteria_assessments)
                        report.passed_criteria = self.check_criteria_assessments(criteria_assessments)

                    # TODO Research question assessments
                    # rq_assessment_corpora = paper.content.get_formatted_content()
                    # report.research_question_assessments = None

                    self.study.reports_collected += 1
                except Exception as e:
                    print(e)

                self.study.papers_collected += 1
                if self.study.papers_collected == batch_size: break
        finally:
            print(f"New papers found: {self.study.papers_collected}")
            self.study.total_runtime = (datetime.now() - self.start_time).total_seconds()
            self.finalize_session()
    
    @staticmethod
    def check_criteria_assessments(criteria_assessments: List[CriteriaAssessment]) -> bool:
        # Check if all inclusion criteria have fulfilled == True
        if not all(ca.fulfilled for ca in criteria_assessments if ca.type == CriteriaType.inclusion):
            return False
        
        # Check if all exclusion criteria have fulfilled == False
        if any(ca.fulfilled for ca in criteria_assessments if ca.type == CriteriaType.exclusion):
            return False
        return True
    
    def format_content_sections(self, content: Content, sections: list[ContentHeaders]=None) -> str:
        section_contents = []
        if sections: sections.sort(key=lambda x: x.value)
        else: sections = list[ContentHeaders]

        for section in sections:
            section_name = section.name.lower()
            if hasattr(content, section_name):
                section_contents.append(f"{section_name}:\n{getattr(content, section_name)}\n")

        return '\n'.join(section_contents)

    def finalize_session(self):
        # Commit the session
        try:
            self.db.session.commit()
            print('All data successfully commited.')
            self.db.session.close()
            print('Database session closed.')
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
        parser.add_argument('--openai_key', type=str, help='Provide the OpenAI key for automated reports.')
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
        # elif not args.openai_key and not os.getenv('OPENAI_API_KEY'):
        #     print(f"Automatic reporting not possible. API key not provided.")
        #     exit(0)
        

        study = StudyRunner(args.study, args.dblp, args.openai_key if args.openai_key else os.getenv('OPENAI_API_KEY'))
        study.run(args.batch) if args.batch else study.run()

        # TODO EXport data to csv depending on flags provided
        if args.export_all:
            pass
        
        if args.export_summary:
            pass

    except Exception as e:
        print(traceback.format_exc())