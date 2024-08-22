import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, JSON, Text, Enum, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class ContentHeaders(enum.Enum):
    tldr = 0
    title = 1
    abstract = 2
    introduction = 3
    methods = 4
    results = 5
    discussion = 6
    references = 7

class LickertScale(enum.Enum):
    _1 = "strongly_disagree"
    _2 = "disagree"
    _3 = "somewhat_disagree"
    _4 = "neither_agree_or_disagree"
    _5 = "somewhat_agree"
    _6 = "agree"
    _7 = "strongly_agree"

class VenueRank(enum.Enum):
    MISSING = 0
    A_STAR  = 1
    A       = 2
    B       = 3
    C       = 4

    @classmethod
    def from_string(cls, string_value : str):
        try:
            if string_value == 'A*':
                return cls.A_STAR
            return cls[string_value.upper()]
        except KeyError:
            return VenueRank.MISSING

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Below are the model for all summary data stored about a study run
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Study(Base):
    __tablename__ = 'studies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)

    study_date = Column(Date, nullable=False)
    dblp_used = Column(String, nullable=False)

    papers_collected = Column(Integer, nullable=False)
    reports_collected = Column(Integer, nullable=True)

    total_tokens_used_llm = Column(Integer, nullable=True)
    total_runtime = Column(Float, default=0.0)  # in seconds

    papers = relationship('Paper', back_populates='study')
    study_input = relationship("StudyInput", back_populates="study")

class StudyInput(Base):
    __tablename__ = 'study_inputs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    study_id = Column(Text, ForeignKey('studies.id'), nullable=False, unique=True)
    
    year_min = Column(Integer, nullable=False)
    year_max = Column(Integer, nullable=False)
    inclusion_criteria = Column(JSON, nullable=False)
    exclusion_criteria = Column(JSON, nullable=False)
    search_word_groups = Column(JSON, nullable=False)

    study_name = Column(String, nullable=True)
    research_goal = Column(Text, nullable=True)
    research_questions = Column(JSON, nullable=True)

    venue_rank_threshold = Column(String, nullable=True)
    accepted_venue_types = Column(JSON, nullable=True)
    manually_accepted_venue_codes = Column(JSON, nullable=True)
    
    study = relationship("Study", back_populates="study_input")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Below are the models that will contain all data of interest per paper
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    study_id = Column(Integer, ForeignKey('studies.id'), nullable=False)
    
    doi = Column(String, nullable=True)
    semantic_scholar_id = Column(String, nullable=True)

    title = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    venue_type = Column(String, nullable=False)
    venue_code = Column(String, nullable=False)
    venue_key = Column(String, nullable=False)
    venue_rank = Column(Enum(VenueRank), nullable=False)

    publisher_source = Column(String, nullable=False)
    pdf_source = Column(String, nullable=True)

    study = relationship('Study', back_populates='papers')
    report = relationship('Report', back_populates='paper')
    content = relationship('Content', back_populates='paper')
    metrics = relationship('Metrics', back_populates='paper')

class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True, autoincrement=True)

    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False, unique=True)
    
    tldr = Column(Text, nullable=True)
    abstract = Column(Text, nullable=True)
    introduction = Column(Text, nullable=True)
    methods = Column(Text, nullable=True)
    results = Column(Text, nullable=True)
    discussion = Column(Text, nullable=True)

    paper = relationship("Paper", back_populates="content")

class Metrics(Base):
    __tablename__ = 'metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)

    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)

    citations = Column(Integer, nullable=True)
    influential_citations = Column(Integer, nullable=True)
    paper_length = Column(Integer, nullable=True)

    paper = relationship("Paper", back_populates="metrics")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Below are the models that contain all the report data collected
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)

    passed_criteria = Column(Boolean, nullable=True)

    paper = relationship('Paper', back_populates='report')
    criteria_assessments = relationship('CriteriaAssessment', back_populates='report', uselist=True)
    research_question_assessments = relationship('ResearchQuestionAssessment', back_populates='report', uselist=True)

class CriteriaAssessment(Base):
    __tablename__ = 'criteria_assessments'
    id = Column(Integer, primary_key=True, autoincrement=True)

    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)

    lickert_value = Column(Enum(LickertScale), nullable=False)
    criteria = Column(Text, nullable=False)
    
    report = relationship("Report", back_populates="criteria_assessments")

class ResearchQuestionAssessment(Base):
    __tablename__ = 'research_question_assessments'
    id = Column(Integer, primary_key=True, autoincrement=True)

    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)

    question = Column(Text, nullable=False)
    answered = Column(Boolean, nullable=False)

    answer = Column(Text, nullable=False)
    paper_extract = Column(Text, nullable=True)

    report = relationship("Report", back_populates="research_question_assessments")
