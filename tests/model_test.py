import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base, Study, StudyInput, Paper, Content, Metrics, Report, CriteriaAssessment, ResearchQuestionAssessment, VenueRank, CriteriaType

@pytest.fixture(scope='module')
def engine():
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope='module')
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='module')
def session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    Session = scoped_session(session_factory)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def test_study_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    assert study.id is not None

def test_study_input_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    study_input = StudyInput(
        study_id=study.id,
        year_min=2000,
        year_max=2023,
        inclusion_criteria={"criteria": "inclusion"},
        exclusion_criteria={"criteria": "exclusion"},
        search_word_groups={"words": ["AI", "ML"]},
        study_name="Study Input 1",
        research_goal="Research Goal",
        research_questions={"questions": ["Q1", "Q2"]},
        venue_rank_threshold="A",
        accepted_venue_types={"types": ["Conference"]},
        manually_accepted_venue_codes={"codes": ["Code1"]}
    )
    session.add(study_input)
    session.commit()

    assert study_input.id is not None

def test_paper_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    paper = Paper(
        study_id=study.id,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)
    session.commit()

    assert paper.id is not None

def test_content_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    paper = Paper(
        study_id=study.id,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)
    session.commit()

    content = Content(
        paper_id=paper.id,
        tldr="TLDR content",
        abstract="Abstract content",
        introduction="Introduction content",
        methods="Methods content",
        results="Results content",
        discussion="Discussion content"
    )
    session.add(content)
    session.commit()

    assert content.id is not None

def test_metrics_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    paper = Paper(
        study_id=study.id,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)
    session.commit()

    metrics = Metrics(
        paper_id=paper.id,
        citations=100,
        influential_citations=10,
        paper_length=15
    )
    session.add(metrics)
    session.commit()

    assert metrics.id is not None

def test_report_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    paper = Paper(
        study_id=study.id,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)
    session.commit()

    report = Report(
        paper_id=paper.id,
        passed_criteria=True
    )
    session.add(report)
    session.commit()

    assert report.id is not None

def test_criteria_assessment_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    paper = Paper(
        study_id=study.id,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)
    session.commit()

    report = Report(
        paper_id=paper.id,
        passed_criteria=True
    )
    session.add(report)
    session.commit()

    criteria_assessment = CriteriaAssessment(
        report_id=report.id,
        type=CriteriaType.inclusion,
        fulfilled=True,
        criteria="Criteria text",
        reason="Reason text"
    )
    session.add(criteria_assessment)
    session.commit()

    assert criteria_assessment.id is not None

def test_research_question_assessment_model(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)
    session.commit()

    paper = Paper(
        study_id=study.id,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)
    session.commit()

    report = Report(
        paper_id=paper.id,
        passed_criteria=True
    )
    session.add(report)
    session.commit()

    research_question_assessment = ResearchQuestionAssessment(
        report_id=report.id,
        question="Research question",
        answered=True,
        answer="Answer text",
        paper_extract="Paper extract text"
    )
    session.add(research_question_assessment)
    session.commit()

    assert research_question_assessment.id is not None

def test_models(session):
    study = Study(
        study_date=datetime.now().date(),
        dblp_used="Yes",
        papers_collected=10,
        reports_collected=5,
        total_tokens_used_llm=1000,
        total_runtime=60.0
    )
    session.add(study)

    study_input = StudyInput(
        study=study,
        year_min=2000,
        year_max=2023,
        inclusion_criteria={"criteria": "inclusion"},
        exclusion_criteria={"criteria": "exclusion"},
        search_word_groups={"words": ["AI", "ML"]},
        study_name="Study Input 1",
        research_goal="Research Goal",
        research_questions={"questions": ["Q1", "Q2"]},
        venue_rank_threshold="A",
        accepted_venue_types={"types": ["Conference"]},
        manually_accepted_venue_codes={"codes": ["Code1"]}
    )
    session.add(study_input)

    paper = Paper(
        study=study,
        doi="10.1234/example.doi",
        semantic_scholar_id="123456",
        title="Example Paper",
        year=2023,
        venue_type="Conference",
        venue_code="Conf2023",
        venue_key="VKey123",
        venue_rank=VenueRank.A,
        publisher_source="Publisher",
        pdf_source="http://example.com/pdf"
    )
    session.add(paper)

    content = Content(
        paper=paper,
        tldr="TLDR content",
        abstract="Abstract content",
        introduction="Introduction content",
        methods="Methods content",
        results="Results content",
        discussion="Discussion content"
    )
    session.add(content)

    metrics = Metrics(
        paper=paper,
        citations=100,
        influential_citations=10,
        paper_length=15
    )
    session.add(metrics)

    report = Report(
        paper=paper,
        passed_criteria=True
    )
    session.add(report)

    criteria_assessment = CriteriaAssessment(
        report=report,
        type=CriteriaType.inclusion,
        fulfilled=True,
        criteria="Criteria text",
        reason="Reason text"
    )
    session.add(criteria_assessment)

    research_question_assessment = ResearchQuestionAssessment(
        report=report,
        question="Research question",
        answered=True,
        answer="Answer text",
        paper_extract="Paper extract text"
    )
    session.add(research_question_assessment)

    session.commit()

    assert study.id is not None
    assert study_input.id is not None
    assert paper.id is not None
    assert content.id is not None
    assert metrics.id is not None
    assert report.id is not None
    assert criteria_assessment.id is not None
    assert research_question_assessment.id is not None
