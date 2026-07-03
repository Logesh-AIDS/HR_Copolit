import uuid
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GoalRecord(Base):
    __tablename__ = "candidate_goals"
    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    goal_details = Column(JSON)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SkillProgressRecord(Base):
    __tablename__ = "skill_progress"
    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    skill_name = Column(String, index=True)
    score = Column(Float)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class LearningPlanRecord(Base):
    __tablename__ = "learning_plans"
    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    plan_content = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MockSessionRecord(Base):
    __tablename__ = "mock_sessions"
    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    session_data = Column(JSON)
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

    def save_learning_plan(self, candidate_id: str, plan_content: dict):
        record = LearningPlanRecord(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            plan_content=plan_content
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def save_mock_session(self, candidate_id: str, session_data: dict):
        record = MockSessionRecord(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            session_data=session_data
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
