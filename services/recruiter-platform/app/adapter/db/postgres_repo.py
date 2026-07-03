import uuid
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PreferenceRecord(Base):
    __tablename__ = "recruiter_preferences"
    id = Column(String, primary_key=True, index=True)
    recruiter_id = Column(String, index=True)
    preferences = Column(JSON)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class SearchRecord(Base):
    __tablename__ = "saved_searches"
    id = Column(String, primary_key=True, index=True)
    recruiter_id = Column(String, index=True)
    query = Column(String)
    filters = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ComparisonRecord(Base):
    __tablename__ = "comparison_sessions"
    id = Column(String, primary_key=True, index=True)
    recruiter_id = Column(String, index=True)
    candidate_ids = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ReportRecord(Base):
    __tablename__ = "generated_reports"
    id = Column(String, primary_key=True, index=True)
    recruiter_id = Column(String, index=True)
    report_type = Column(String)
    content = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PostgresRepository:
    def __init__(self, db_session):
        self.db = db_session

    def save_comparison_session(self, recruiter_id: str, candidate_ids: list):
        record = ComparisonRecord(
            id=str(uuid.uuid4()),
            recruiter_id=recruiter_id,
            candidate_ids=candidate_ids
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def save_report(self, recruiter_id: str, report_type: str, content: dict):
        record = ReportRecord(
            id=str(uuid.uuid4()),
            recruiter_id=recruiter_id,
            report_type=report_type,
            content=content
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
