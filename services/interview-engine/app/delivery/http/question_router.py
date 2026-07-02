# services/interview-engine/app/delivery/http/question_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.question_repo import QuestionRepository
from app.adapter.vector.question_qdrant_repo import QuestionQdrantRepository
from app.domain.services.question_service import QuestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["AI Question Intelligence Engine"])

def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    repo = QuestionRepository(db)
    vector_repo = QuestionQdrantRepository()
    return QuestionService(repo, vector_repo)


class QuestionAddPayload(BaseModel):
    category: str = Field(..., description="Target category (Programming, Algorithms, DevOps)")
    subcategory: Optional[str] = Field(None, description="Subtopic concepts")
    difficulty: str = Field(..., description="Tuning level (JUNIOR, MID, SENIOR, PRINCIPAL)")
    statement: str = Field(..., description="Question statement details")
    required_skills: List[str] = Field(default=[], description="Skills taxonomy tags")
    hints: List[str] = Field(default=[], description="Hints lists")
    reference_solution: Optional[str] = Field(None, description="Solution template")


class AdaptiveEvaluatePayload(BaseModel):
    session_id: str = Field(..., description="Interview Session ID")
    current_difficulty: str = Field(..., description="Active level scale")
    previous_score: float = Field(..., description="Score awarded for previous answer")


@router.post("/add", status_code=status.HTTP_201_CREATED)
def add_question(
    payload: QuestionAddPayload,
    service: QuestionService = Depends(get_question_service)
):
    try:
        q = service.add_question(
            category=payload.category,
            subcategory=payload.subcategory,
            difficulty=payload.difficulty,
            statement=payload.statement,
            required_skills=payload.required_skills,
            hints=payload.hints,
            reference_solution=payload.reference_solution
        )
        return make_success_response({
            "question_id": str(q.id),
            "category": q.category,
            "difficulty": q.difficulty,
            "status": "ADDED"
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
def search_questions(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    service: QuestionService = Depends(get_question_service)
):
    qs = service.search_questions(category, difficulty, search_term)
    return make_success_response([
        {
            "id": str(q.id),
            "category": q.category,
            "subcategory": q.subcategory,
            "difficulty": q.difficulty,
            "problem_statement": q.problem_statement,
            "metadata": q.question_metadata
        } for q in qs
    ])


@router.get("/next/{session_id}")
def get_next_question(
    session_id: str,
    skills: str = Query("", description="Comma-separated query tags list"),
    category: str = Query("Programming"),
    difficulty: str = Query("MID"),
    service: QuestionService = Depends(get_question_service)
):
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    try:
        q = service.get_next_question(session_id, skills_list, category, difficulty)
        return make_success_response({
            "question_id": str(q.id),
            "category": q.category,
            "subcategory": q.subcategory,
            "difficulty": q.difficulty,
            "problem_statement": q.problem_statement,
            "hints": q.question_metadata.get("hints", [])
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch next question: {e}")


@router.get("/followups/{question_id}")
def get_followups(
    question_id: str,
    service: QuestionService = Depends(get_question_service)
):
    try:
        hints = service.get_followups(question_id)
        return make_success_response(hints)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/adapt")
def evaluate_adaptive_scaling(
    payload: AdaptiveEvaluatePayload,
    service: QuestionService = Depends(get_question_service)
):
    try:
        new_difficulty = service.adapt_difficulty(
            session_id=payload.session_id,
            current_difficulty=payload.current_difficulty,
            previous_score=payload.previous_score
        )
        return make_success_response({
            "session_id": payload.session_id,
            "previous_difficulty": payload.current_difficulty,
            "adapted_difficulty": new_difficulty
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
