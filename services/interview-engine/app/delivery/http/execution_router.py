# services/interview-engine/app/delivery/http/execution_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException, Request
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.execution_repo import ExecutionRepository
from app.adapter.db.interview_repo import InterviewRepository
from app.domain import execution_models
from app.domain.services.execution_service import ExecutionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["AI Interview Execution Engine"])

def get_execution_service(db: Session = Depends(get_db)) -> ExecutionService:
    repo = ExecutionRepository(db)
    plan_repo = InterviewRepository(db)
    return ExecutionService(repo, plan_repo)


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_session(
    payload: execution_models.CreateSessionPayload,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Creates an execution session mapping to an interview plan blueprint.
    """
    try:
        sess = service.create_session(
            application_id=payload.application_id,
            plan_id=payload.interview_plan_id
        )
        return make_success_response({
            "session_id": str(sess.id),
            "session_token": sess.session_token,
            "status": sess.status
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start/{session_id}")
def start_session(
    session_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Starts the active execution session, initializing timers and rounds.
    """
    try:
        sess = service.start_session(session_id)
        return make_success_response({
            "session_id": str(sess.id),
            "status": sess.status,
            "connection_status": sess.runtime_state.connection_status if sess.runtime_state else "DISCONNECTED"
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pause/{session_id}")
def pause_session(
    session_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Pauses an active interview session execution.
    """
    try:
        sess = service.pause_session(session_id)
        return make_success_response({
            "session_id": str(sess.id),
            "status": sess.status,
            "pause_count": sess.runtime_state.pause_count if sess.runtime_state else 0
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/resume/{session_id}")
def resume_session(
    session_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Resumes a paused interview session execution.
    """
    try:
        sess = service.resume_session(session_id)
        return make_success_response({
            "session_id": str(sess.id),
            "status": sess.status
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reconnect")
def reconnect_session(
    payload: execution_models.ReconnectPayload,
    request: Request,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Authenticates and recovers an interrupted session via token validation.
    """
    try:
        ip = payload.ip_address or request.client.host if request.client else None
        ua = payload.user_agent or request.headers.get("user-agent")
        
        sess = service.reconnect_session(
            session_token=payload.session_token,
            ip=ip,
            ua=ua
        )
        return make_success_response({
            "session_id": str(sess.id),
            "status": sess.status,
            "connection_status": sess.runtime_state.connection_status if sess.runtime_state else "DISCONNECTED"
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/terminate/{session_id}")
def terminate_session(
    session_id: str,
    success: bool = Query(True, description="Verdict indicating if candidate completed or failed session constraints"),
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Force terminates the execution session.
    """
    try:
        verdict = "FINISHED" if success else "FAILED"
        sess = service.terminate_session(session_id, verdict)
        return make_success_response({
            "session_id": str(sess.id),
            "status": sess.status
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/state/{session_id}")
def get_session_state(
    session_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Retrieves full execution runtime metrics, pointers, and variables.
    """
    sess = service.repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")

    state = sess.runtime_state
    return make_success_response({
        "id": str(sess.id),
        "application_id": str(sess.application_id),
        "interview_plan_id": str(sess.interview_plan_id) if sess.interview_plan_id else None,
        "session_token": sess.session_token,
        "status": sess.status,
        "current_round_index": state.current_round_index if state else 0,
        "current_question_index": state.current_question_index if state else 0,
        "current_difficulty": state.current_difficulty if state else "MEDIUM",
        "current_score": state.current_score if state else 0.0,
        "remaining_time_seconds": state.remaining_time_seconds if state else 3600,
        "connection_status": state.connection_status if state else "DISCONNECTED",
        "warnings_count": state.warnings_count if state else 0,
        "pause_count": state.pause_count if state else 0,
        "reconnect_attempts": state.reconnect_attempts if state else 0
    })


@router.get("/timeline/{session_id}")
def get_session_timeline(
    session_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Returns log sequence audit path tracing all timeline transitions.
    """
    sess = service.repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")

    timeline = [
        {
            "event_type": e.event_type,
            "message": e.message,
            "payload": e.payload,
            "created_at": e.created_at
        } for e in sess.events
    ]
    return make_success_response(timeline)


@router.get("/progress/{session_id}")
def get_session_progress(
    session_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """
    Fetches round progress metrics.
    """
    sess = service.repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")

    rounds = [
        {
            "round_index": rp.round_index,
            "round_name": rp.round_name,
            "status": rp.status,
            "time_spent_seconds": rp.time_spent_seconds,
            "score_awarded": rp.score_awarded,
            "completed_at": rp.completed_at
        } for rp in sorted(sess.round_progress, key=lambda x: x.round_index)
    ]
    return make_success_response(rounds)
