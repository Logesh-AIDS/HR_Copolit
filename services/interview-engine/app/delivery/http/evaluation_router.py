# services/interview-engine/app/delivery/http/evaluation_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.evaluation_repo import EvaluationRepository
from app.domain.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluate", tags=["AI Answer Evaluation Engine"])

def get_evaluation_service(db: Session = Depends(get_db)) -> EvaluationService:
    repo = EvaluationRepository(db)
    return EvaluationService(repo)


class EvaluateAnswerPayload(BaseModel):
    session_id: str = Field(..., description="Active session identity")
    question_id: str = Field(..., description="Target question identifier")
    candidate_answer: str = Field(..., description="Candidate response text transcript")
    config: Optional[dict] = Field(None, description="Optional pipeline weights configurations")


class ReEvaluatePayload(BaseModel):
    role: str = Field(..., description="Changer role e.g. RECRUITER or ADMINISTRATOR")
    new_score: float = Field(..., description="Adjusted score value")
    reason: str = Field(..., description="Reasoning explanations details")


@router.post("/answer", status_code=status.HTTP_201_CREATED)
def evaluate_answer(
    payload: EvaluateAnswerPayload,
    service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        ev = service.evaluate_answer(
            session_id=payload.session_id,
            question_id=payload.question_id,
            candidate_answer=payload.candidate_answer,
            config=payload.config
        )
        return make_success_response({
            "evaluation_id": str(ev.id),
            "session_id": str(ev.session_id),
            "question_id": str(ev.question_id),
            "overall_score": ev.overall_score,
            "status": "EVALUATED"
        })
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to evaluate answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error evaluating answer")


@router.get("/answer/{evaluation_id}")
def retrieve_evaluation(
    evaluation_id: str,
    service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        rep = service.get_report(evaluation_id)
        return make_success_response(rep)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/feedback/{evaluation_id}")
def retrieve_feedback(
    evaluation_id: str,
    service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        rep = service.get_report(evaluation_id)
        return make_success_response(rep["feedback"])
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/breakdown/{evaluation_id}")
def retrieve_score_breakdown(
    evaluation_id: str,
    service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        rep = service.get_report(evaluation_id)
        return make_success_response({
            "overall_score": rep["overall_score"],
            "rubrics": rep["rubrics"],
            "reasoning": rep["reasoning"],
            "similarity": rep["similarity"]
        })
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reevaluate/{evaluation_id}")
def reevaluate_answer(
    evaluation_id: str,
    payload: ReEvaluatePayload,
    service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        ev = service.re_evaluate_answer(
            eval_id=evaluation_id,
            role=payload.role,
            new_score=payload.new_score,
            reason=payload.reason
        )
        return make_success_response({
            "evaluation_id": str(ev.id),
            "overall_score": ev.overall_score,
            "status": "RE_EVALUATED"
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))
