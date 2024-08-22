from datetime import datetime, date
import traceback
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Type
from sqlalchemy import create_engine, cast
from database.models import Base, Paper, Content, ContentHeaders, Metrics, Study, Report, CriteriaAssessment, LickertScale
from sqlalchemy.orm import DeclarativeBase

class DatabaseManager:
    def __init__(self):
        # Create an engine that stores data in the local directory's
        # papers.db file.
        self.engine = create_engine('sqlite:///papers.db')
        # Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
        Base.metadata.create_all(self.engine)
        # Create a configured "Session" class
        Session = sessionmaker(bind=self.engine)

        # Create a Session
        self.session = Session()

    def show_paper_pdf_links(self, study_id: str) -> List[str]:
        papers_info = []
        papers = self.get_study_papers(study_id)
        if papers:
            for paper in papers:
                papers_info.append(f"Paper Title: {paper.title} | Link: {paper.pdf_source if paper.pdf_source else paper.publisher_source}")
        return papers_info
    
    def show_table_statistics(self, table_class: Type[DeclarativeBase]) -> str:        
        return f'''Table: {str(table_class)} 
        | Total Entries: {self.session.query(table_class).count()} 
        | Entry attributes: {[k for k, v in table_class.__dict__.items() if not callable(v) and not k.startswith('_')]}'''

    def show_studies_of_date(self, study_date: str=None) -> List[str]:
        studies = []
        for study in self.session.query(Study).filter(str(Study.study_date) == (study_date if study_date else str(datetime.now().date()))):
            studies.append(f"Date {study.study_date} | ID: {study.id} | Papers: {study.papers_collected} | Reports: {study.reports_collected}")
        return studies

    def get_study(self, study_id: str) -> Optional[Study]:
        return self.session.query(Study).filter(Study.id == study_id).one_or_none()
    
    def get_study_papers(self, study_id: str) -> Optional[List[Paper]]:
        study = self.session.query(Study).filter(Study.id == study_id).one_or_none()
        return study.papers if study else None
    
    def get_papers_with_passed_criteria_by_study_id(self, study_id: int):
        return self.session.query(Paper).join(Report).filter(
            Paper.study_id == study_id,
            Report.passed_criteria == True
        ).all()
    
    # Fix
    def get_study_reports(self, study_id: str) -> Optional[List[Report]]:
        study = self.session.query(Study).filter(Study.id == study_id).one_or_none()
        return study if study else None

    def get_all_papers(self) -> List[Paper]:
        return self.session.query(Paper).all()
    
    def get_paper_report(self, paper_id: str) -> Optional[Report]:
        return self.session.query(Report).filter(Report.paper_id == paper_id).one_or_none()
    
    def get_report_criteria_assessments(self, report_id: str) -> Optional[List[CriteriaAssessment]]:
        return self.session.query(CriteriaAssessment).filter(CriteriaAssessment.report_id == report_id).all()

    # Checks if the paper is already in the db and return it for populating or keep the current paper
    def load_local_paper(self, paper : Paper) -> Paper:
        prev_stored_entry = None
        if paper.doi:
            prev_stored_entry : Paper = self.session.query(Paper).filter(Paper.doi == paper.doi).one_or_none()
        elif paper.semantic_scholar_id:
            prev_stored_entry : Paper = self.session.query(Paper).filter(Paper.semantic_scholar_id == paper.semantic_scholar_id).one_or_none()
        return prev_stored_entry if prev_stored_entry else paper
