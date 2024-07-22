from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models_old import Study, ResearchPaper, VenueRank, Report, CriteriaAssessment, CriteriaType, ResearchQuestionAssessment
from datetime import datetime

# Assuming your database URI is set up correctly
DATABASE_URI = 'sqlite:///research_papers.db'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Step 1: Create a new study
new_study = Study(
    study_date=datetime.now().date(),
    dblp_used='Some DBLP Source',
    papers_collected=10,
    analyses_collected=5,
    total_tokens_used_llm=1000,
    total_runtime=3600.0
)

# Step 2: Create research papers and associate them with the study
papers = [
    ResearchPaper(
        doi='10.1000/j.journal.2023.01',
        semantic_scholar_id='some_id_1',
        title='Paper 1 Title',
        year=2023,
        venue_type='Conference',
        venue_code='Conf2023',
        venue_key='Conf2023Key',
        venue_rank=VenueRank.A_STAR,
        publisher_source='Publisher 1',
        pdf_source='http://example.com/pdf1'
    ),
    ResearchPaper(
        doi='10.1000/j.journal.2023.02',
        semantic_scholar_id='some_id_2',
        title='Paper 2 Title',
        year=2023,
        venue_type='Journal',
        venue_code='Jour2023',
        venue_key='Jour2023Key',
        venue_rank=VenueRank.A,
        publisher_source='Publisher 2',
        pdf_source='http://example.com/pdf2'
    )
]

# Add papers to the study
new_study.research_papers.extend(papers)

# Step 3: Create reports for each paper and associate them with the study
reports = []
for paper in papers:
    report = Report(
        study=new_study,
        research_paper=paper,
        passed_criteria=True
    )
    
    criteria_assessment = CriteriaAssessment(
        type=CriteriaType.inclusion,
        fulfilled=True,
        criteria='Criteria 1',
        reason='Reason for inclusion'
    )
    
    research_question_assessment = ResearchQuestionAssessment(
        question='Research Question 1',
        answered=True,
        answer='Answer to research question 1',
        paper_extract='Extract from the paper'
    )
    
    report.criteria_assessments.append(criteria_assessment)
    report.research_question_assessments.append(research_question_assessment)
    
    reports.append(report)

# Add reports to the session
session.add(new_study)
session.add_all(papers)
session.add_all(reports)

# Commit the transaction
session.commit()

# Close the session
session.close()
