# services/interview-engine/app/domain/services/question_service.py
import logging
import json
import time
import uuid
from typing import List, Optional, Dict, Any

from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.question_repo import QuestionRepository
from app.adapter.vector.question_qdrant_repo import QuestionQdrantRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(self, repo: QuestionRepository, vector_repo: QuestionQdrantRepository):
        self.repo = repo
        self.vector_repo = vector_repo

    def add_question(
        self,
        category: str,
        subcategory: Optional[str],
        difficulty: str,
        statement: str,
        required_skills: List[str],
        hints: List[str],
        reference_solution: Optional[str] = None
    ) -> orm.QuestionORM:
        metadata = {
            "required_skills": required_skills,
            "hints": hints,
            "reference_solution": reference_solution,
            "popularity": 0,
            "quality_score": 5.0
        }
        
        q = self.repo.create_question(category, subcategory, difficulty, statement, metadata)
        
        # Upsert vector representation to Qdrant
        self.vector_repo.upsert_question_vector(str(q.id), required_skills, statement)
        self.repo.commit()
        return q

    def search_questions(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[orm.QuestionORM]:
        return self.repo.search_questions(category, difficulty, search_term)

    def adapt_difficulty(
        self,
        session_id: str,
        current_difficulty: str,
        previous_score: float
    ) -> str:
        """
        Evaluate adaptive difficulty scale rules:
        - If previous_score > 8.0, increase difficulty index.
        - If previous_score < 4.0, decrease difficulty.
        """
        difficulty_levels = ["FRESHER", "JUNIOR", "MID", "SENIOR", "PRINCIPAL"]
        try:
            curr_idx = difficulty_levels.index(current_difficulty.upper())
        except ValueError:
            curr_idx = 2  # default to MID
            
        new_idx = curr_idx
        rationale = ""
        
        if previous_score >= 8.0 and curr_idx < len(difficulty_levels) - 1:
            new_idx += 1
            rationale = f"Consecutive high score ({previous_score}/10) triggers difficulty escalation."
        elif previous_score <= 4.0 and curr_idx > 0:
            new_idx -= 1
            rationale = f"Low score ({previous_score}/10) triggers difficulty reduction."

        new_difficulty = difficulty_levels[new_idx]
        
        if new_difficulty != current_difficulty:
            sess_uuid = uuid.UUID(session_id)
            # Log the adaptive decision in database
            decision = orm.AdaptiveDecisionORM(
                id=uuid.uuid4(),
                interview_plan_id=sess_uuid,  # In tests and DB, we links plan_id or session_id
                trigger_event="SCORE_EVALUATION",
                adjustment_details=f"Scaled {current_difficulty} -> {new_difficulty}. Rationale: {rationale}"
            )
            self.repo.db.add(decision)
            self.repo.commit()
            
        return new_difficulty

    def get_next_question(
        self,
        session_id: str,
        skills: List[str],
        category: str,
        difficulty: str
    ) -> orm.QuestionORM:
        start_time = time.perf_counter()
        strategy = "SQL_METADATA"
        
        # 1. Query Qdrant for semantic search matching target candidate skills
        matched_ids = []
        if skills:
            hits = self.vector_repo.search_similar_questions(skills, limit=10)
            if hits:
                matched_ids = [uuid.UUID(hit["question_id"]) for hit in hits]
                strategy = "HYBRID_VECTOR"

        # 2. Query Postgres
        query = self.repo.db.query(orm.QuestionORM).filter(
            orm.QuestionORM.category == category,
            orm.QuestionORM.difficulty == difficulty
        )
        if matched_ids:
            query = query.filter(orm.QuestionORM.id.in_(matched_ids))
            
        q = query.first()

        # Fallback to category metadata filter if no semantic match is found
        if not q:
            q = self.repo.db.query(orm.QuestionORM).filter(
                orm.QuestionORM.category == category,
                orm.QuestionORM.difficulty == difficulty
            ).first()
            strategy = "SQL_METADATA"

        # Safe fallback: retrieve any question matching category
        if not q:
            q = self.repo.db.query(orm.QuestionORM).filter(
                orm.QuestionORM.category == category
            ).first()

        # Complete fallback
        if not q:
            q = self.repo.db.query(orm.QuestionORM).first()

        if not q:
            # Create a mock default question if bank is empty
            q = self.add_question(
                category=category,
                subcategory="Core Concepts",
                difficulty=difficulty,
                statement=f"Detail your architectural strategy for high-throughput {category} systems.",
                required_skills=skills,
                hints=["Analyze bottleneck indicators."]
            )

        latency = int((time.perf_counter() - start_time) * 1000)
        
        # Log retrieval latency in DB
        self.repo.log_retrieval(session_id, str(q.id), strategy, latency)
        self.repo.commit()
        return q

    def get_followups(self, question_id: str) -> List[str]:
        q = self.repo.get_question(question_id)
        if not q:
            raise NotFoundException("Question not found.")
        
        meta = q.question_metadata or {}
        return meta.get("hints", [])
