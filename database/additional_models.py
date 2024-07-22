import uuid, enum
from sqlalchemy import Enum, Date, Column, Integer, String, Text, ForeignKey, JSON, DateTime, Table, Float, Boolean, event
from sqlalchemy.orm import declarative_base, relationship, declared_attr
from datetime import datetime
from typing import List

Base = declarative_base()

class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.now, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
# Based on PRISMA flow https://www.prisma-statement.org/s/PRISMA_2020_flow_diagram_new_SRs_v1-x4tp.docx
class PrismaSummary(Base):
    __tablename__ = 'prisma_summaries'
    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))

    study_id = Column(Text, ForeignKey('studies.id'), nullable=False, unique=True)

    # IDENTIFICATION
    # Records identified from databases and registers
    total_papers_collected = Column(Integer, nullable=False)

    # Records removed before screening:
    duplicate_records_removed = Column(Integer, nullable=False)
    records_refused_by_aux_filters = Column(Integer, nullable=False)
    records_refused_by_automated_filters = Column(Integer, nullable=False)

    # SCREENING

    # Papers
    records_screened = Column(Integer, nullable=False)
    records_excluded_manually = Column(Integer, nullable=False)
    records_excluded_automatically = Column(Integer, nullable=False)

    # Paper reports
    report_construction_attempts = Column(Integer, nullable=False)
    report_construction_failures = Column(Integer, nullable=False)
    report_assessment_attempts = Column(Integer, nullable=False)
    report_assessment_exclusions = Column(Integer, nullable=False)
    report_assessment_exclusion_summaries = Column(Integer, nullable=False)

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))

    name = Column(String, nullable=False)
    research_papers = relationship("ResearchPaper", back_populates="authors")