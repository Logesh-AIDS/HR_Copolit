# services/interview-engine/app/delivery/http/orchestrator_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.interview_repo import InterviewRepository
from app.domain import interview_models
from app.domain.services.orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["AI Interview Orchestrator"])

def get_orchestrator_service(db: Session = Depends(get_db)) -> OrchestratorService:
    repo = InterviewRepository(db)
    return OrchestratorService(repo)


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_interview(
    payload: interview_models.GeneratePlanPayload,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Consumes candidate intelligence and job description parameters to generate an adaptive Interview Plan.
    """
    try:
        plan = service.generate_interview_blueprint(
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            company_config=payload.company_config,
            recruiter_preferences=payload.recruiter_preferences
        )
        return make_success_response({
            "plan_id": str(plan.id),
            "role": plan.role,
            "difficulty": plan.difficulty,
            "status": plan.status,
            "rounds_count": len(plan.blueprint.rounds) if plan.blueprint else 0
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start/{plan_id}")
def start_interview(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Activates the generated Interview Plan.
    """
    plan = service.start_interview(plan_id)
    return make_success_response({
        "plan_id": str(plan.id),
        "status": plan.status,
        "connection_status": plan.execution_state.connection_status
    })


@router.post("/pause/{plan_id}")
def pause_interview(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Pauses an active interview session.
    """
    plan = service.pause_interview(plan_id)
    return make_success_response({
        "plan_id": str(plan.id),
        "is_paused": plan.execution_state.is_paused
    })


@router.post("/resume/{plan_id}")
def resume_interview(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Resumes a paused interview session.
    """
    plan = service.resume_interview(plan_id)
    return make_success_response({
        "plan_id": str(plan.id),
        "is_paused": plan.execution_state.is_paused,
        "connection_status": plan.execution_state.connection_status
    })


@router.post("/next-question/{plan_id}")
def next_question(
    plan_id: str,
    question_score: float = Query(..., description="The score awarded for the answer (0.0 to 10.0)"),
    skipped: bool = Query(False, description="Flag indicating if the candidate skipped the question"),
    warning_message: Optional[str] = Query(None, description="Optional warning telemetry from the proctoring modules"),
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Submits answer parameters, shifts pointers, and triggers adaptive difficulty recalibrations.
    """
    plan = service.submit_answer_and_adapt(
        plan_id=plan_id,
        question_score=question_score,
        skipped=skipped,
        warning_message=warning_message
    )
    state = plan.execution_state
    
    # Fetch active round details safely
    rounds_list = sorted(plan.blueprint.rounds, key=lambda r: r.round_index)
    current_round = rounds_list[state.current_round_index] if state.current_round_index < len(rounds_list) else None

    return make_success_response({
        "plan_id": str(plan.id),
        "current_round_index": state.current_round_index,
        "current_question_index": state.current_question_index,
        "score": state.score,
        "active_round_difficulty": current_round.difficulty if current_round else "COMPLETED",
        "is_completed": state.is_completed
    })


@router.post("/next-round/{plan_id}")
def next_round(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Force steps pointer to the next round block.
    """
    plan = service.repo.get_interview_plan(plan_id)
    if not plan or not plan.execution_state:
        raise NotFoundException("Target interview plan not found.")

    state = plan.execution_state
    rounds_list = sorted(plan.blueprint.rounds, key=lambda r: r.round_index)

    state.current_question_index = 0
    state.current_round_index += 1

    if state.current_round_index >= len(rounds_list):
        state.is_completed = True
        plan.status = "COMPLETED"
    
    service.repo.commit()
    return make_success_response({
        "plan_id": str(plan.id),
        "current_round_index": state.current_round_index,
        "is_completed": state.is_completed
    })


@router.get("/plan/{plan_id}")
def get_interview_plan(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Retrieves full blueprint structures, rounds lists, and configurations.
    """
    plan = service.repo.get_interview_plan(plan_id)
    if not plan:
        raise NotFoundException("Interview plan not found.")

    return make_success_response({
        "id": str(plan.id),
        "candidate_id": str(plan.candidate_id),
        "job_id": str(plan.job_id),
        "candidate_level": plan.candidate_level,
        "role": plan.role,
        "difficulty": plan.difficulty,
        "total_duration_minutes": plan.total_duration_minutes,
        "passing_criteria": plan.passing_criteria,
        "status": plan.status,
        "blueprint": {
            "name": plan.blueprint.name,
            "rounds_count": plan.blueprint.rounds_count,
            "rounds": [
                {
                    "round_index": r.round_index,
                    "name": r.name,
                    "objective": r.objective,
                    "category": r.category,
                    "difficulty": r.difficulty,
                    "max_time_minutes": r.max_time_minutes,
                    "question_count": r.question_count
                } for r in sorted(plan.blueprint.rounds, key=lambda rd: rd.round_index)
            ]
        } if plan.blueprint else None,
        "execution_state": {
            "current_round_index": plan.execution_state.current_round_index,
            "current_question_index": plan.execution_state.current_question_index,
            "remaining_time_seconds": plan.execution_state.remaining_time_seconds,
            "score": plan.execution_state.score,
            "is_paused": plan.execution_state.is_paused,
            "is_completed": plan.execution_state.is_completed,
            "is_failed": plan.execution_state.is_failed
        } if plan.execution_state else None
    })


@router.get("/timeline/{plan_id}")
def get_interview_timeline(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Returns audit timeline log entries tracking execution milestones.
    """
    plan = service.repo.get_interview_plan(plan_id)
    if not plan:
        raise NotFoundException("Interview plan not found.")

    timeline = [
        {
            "event_type": t.event_type,
            "message": t.message,
            "timestamp": t.timestamp
        } for t in plan.timelines
    ]
    return make_success_response(timeline)


@router.post("/finish/{plan_id}")
def finish_interview(
    plan_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Force terminates or finalizes the active interview, calculating pass verdicts.
    """
    plan = service.finish_interview(plan_id)
    return make_success_response({
        "plan_id": str(plan.id),
        "status": plan.status,
        "score": plan.execution_state.score,
        "verdict": "PASSED" if plan.status == "COMPLETED" else "FAILED"
    })
