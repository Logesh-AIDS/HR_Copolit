# services/interview-engine/app/adapter/db/question_repo.py
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_question(
        self,
        category: str,
        subcategory: Optional[str],
        difficulty: str,
        statement: str,
        metadata: dict
    ) -> orm.QuestionORM:
        q = orm.QuestionORM(
            id=uuid.uuid4(),
            category=category,
            subcategory=subcategory,
            difficulty=difficulty,
            problem_statement=statement,
            question_metadata=metadata
        )
        self.db.add(q)
        self.db.flush()
        return q

    def get_question(self, question_id: str) -> Optional[orm.QuestionORM]:
        try:
            q_uuid = uuid.UUID(question_id)
            return self.db.query(orm.QuestionORM).filter(orm.QuestionORM.id == q_uuid).first()
        except ValueError:
            return None

    def search_questions(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[orm.QuestionORM]:
        query = self.db.query(orm.QuestionORM)
        
        if category:
            query = query.filter(orm.QuestionORM.category == category)
        if difficulty:
            query = query.filter(orm.QuestionORM.difficulty == difficulty)
        if search_term:
            query = query.filter(
                or_(
                    orm.QuestionORM.problem_statement.ilike(f"%{search_term}%"),
                    orm.QuestionORM.category.ilike(f"%{search_term}%")
                )
            )
            
        return query.all()

    def create_rubric(
        self,
        question_id: str,
        criteria: str,
        max_score: float,
        description: Optional[str] = None
    ) -> orm.QuestionRubricORM:
        rubric = orm.QuestionRubricORM(
            id=uuid.uuid4(),
            question_id=uuid.UUID(question_id),
            criteria=criteria,
            max_score=max_score,
            description=description
        )
        self.db.add(rubric)
        self.db.flush()
        return rubric

    def create_version(
        self,
        question_id: str,
        version_number: int,
        statement: str
    ) -> orm.QuestionVersionORM:
        v = orm.QuestionVersionORM(
            id=uuid.uuid4(),
            question_id=uuid.UUID(question_id),
            version_number=version_number,
            statement_snapshot=statement
        )
        self.db.add(v)
        self.db.flush()
        return v

    def log_retrieval(
        self,
        session_id: str,
        question_id: str,
        strategy: str,
        latency_ms: int
    ) -> orm.QuestionRetrievalLogORM:
        log = orm.QuestionRetrievalLogORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            question_id=uuid.UUID(question_id),
            retrieval_strategy=strategy,
            latency_ms=latency_ms
        )
        self.db.add(log)
        self.db.flush()
        return log

    def commit(self):
        self.db.commit()
