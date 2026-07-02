# services/interview-engine/app/domain/services/execution_service.py
import logging
import uuid
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.sql import func

from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.execution_repo import ExecutionRepository
from app.adapter.db.interview_repo import InterviewRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS = {
    "CREATED": {"WAITING", "CANCELLED", "STARTED"},
    "WAITING": {"READY", "CANCELLED", "STARTED"},
    "READY": {"STARTED", "CANCELLED"},
    "STARTED": {"ROUND_RUNNING", "PAUSED", "CANCELLED", "DISCONNECTED", "FINISHED", "FAILED"},
    "ROUND_RUNNING": {"QUESTION_RUNNING", "PAUSED", "FINISHED", "CANCELLED", "DISCONNECTED", "FAILED"},
    "QUESTION_RUNNING": {"ROUND_RUNNING", "PAUSED", "FINISHED", "CANCELLED", "DISCONNECTED", "FAILED"},
    "PAUSED": {"RESUMED", "CANCELLED", "FAILED"},
    "RESUMED": {"ROUND_RUNNING", "QUESTION_RUNNING", "DISCONNECTED", "CANCELLED", "FAILED"},
    "DISCONNECTED": {"RECOVERING", "FAILED", "FINISHED"},
    "RECOVERING": {"ROUND_RUNNING", "QUESTION_RUNNING", "FAILED", "FINISHED"},
    "FINISHED": set(),
    "CANCELLED": set(),
    "FAILED": set()
}

class ExecutionService:
    """
    Core state coordinator governing live interview execution sessions, state transitions,
    timer synchronization ticks, and browser recovery operations.
    """
    def __init__(self, repo: ExecutionRepository, plan_repo: InterviewRepository):
        self.repo = repo
        self.plan_repo = plan_repo

    def validate_transition(self, from_state: str, to_state: str):
        allowed = ALLOWED_TRANSITIONS.get(from_state, set())
        if to_state not in allowed:
            raise ValidationException(f"Invalid state transition: {from_state} -> {to_state} is prohibited.")

    def create_session(self, application_id: str, plan_id: str) -> orm.InterviewSessionORM:
        plan = self.plan_repo.get_interview_plan(plan_id)
        if not plan:
            raise NotFoundException("Interview plan blueprint not found.")

        # Generate cryptographic session token
        session_token = f"sess_{secrets.token_urlsafe(32)}"
        session = self.repo.create_session(
            application_id=application_id,
            interview_plan_id=plan_id,
            session_token=session_token
        )
        
        # Log initial transition
        self.repo.log_state_transition(str(session.id), "NONE", "CREATED")
        self.repo.log_runtime_event(
            session_id=str(session.id),
            event_type="InterviewInitialized",
            message=f"Created session mapping to plan: {plan_id}",
            payload={"application_id": application_id}
        )
        self.repo.commit()
        return session

    def start_session(self, session_id: str) -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session:
            raise NotFoundException("Session not found.")

        self.validate_transition(session.status, "STARTED")
        
        old_status = session.status
        session.status = "STARTED"
        session.started_at = func.now()
        
        runtime = session.runtime_state
        if runtime:
            runtime.connection_status = "CONNECTED"
            if session.interview_plan:
                runtime.remaining_time_seconds = session.interview_plan.total_duration_minutes * 60

        # Log state transition
        self.repo.log_state_transition(session_id, old_status, "STARTED")

        # Initialize round progress metrics
        if session.interview_plan and session.interview_plan.blueprint:
            for r_def in session.interview_plan.blueprint.rounds:
                prog = orm.RoundProgressORM(
                    id=uuid.uuid4(),
                    interview_session_id=session.id,
                    round_index=r_def.round_index,
                    round_name=r_def.name,
                    status="PENDING"
                )
                self.repo.db.add(prog)

        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="InterviewStarted",
            message="Interview session started and timers initiated.",
            payload={"remaining_time_seconds": runtime.remaining_time_seconds if runtime else 3600}
        )
        self.repo.commit()
        return session

    def start_round(self, session_id: str, round_index: int) -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            raise NotFoundException("Session not found.")

        self.validate_transition(session.status, "ROUND_RUNNING")
        old_status = session.status
        session.status = "ROUND_RUNNING"
        session.runtime_state.current_round_index = round_index
        session.runtime_state.current_question_index = 0

        # Update round progress state
        for r_prog in session.round_progress:
            if r_prog.round_index == round_index:
                r_prog.status = "ACTIVE"

        self.repo.log_state_transition(session_id, old_status, "ROUND_RUNNING")
        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="RoundStarted",
            message=f"Round index {round_index} started.",
            payload={"round_index": round_index}
        )
        self.repo.commit()
        return session

    def start_question(self, session_id: str, question_index: int) -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            raise NotFoundException("Session not found.")

        self.validate_transition(session.status, "QUESTION_RUNNING")
        old_status = session.status
        session.status = "QUESTION_RUNNING"
        session.runtime_state.current_question_index = question_index

        # Add question progress trace
        qp = orm.QuestionProgressORM(
            id=uuid.uuid4(),
            interview_session_id=session.id,
            round_index=session.runtime_state.current_round_index,
            question_index=question_index,
            difficulty=session.runtime_state.current_difficulty,
            score=0.0
        )
        self.repo.db.add(qp)

        self.repo.log_state_transition(session_id, old_status, "QUESTION_RUNNING")
        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="QuestionStarted",
            message=f"Question index {question_index} started.",
            payload={"question_index": question_index}
        )
        self.repo.commit()
        return session

    def pause_session(self, session_id: str) -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            raise NotFoundException("Session not found.")

        self.validate_transition(session.status, "PAUSED")
        
        old_status = session.status
        session.status = "PAUSED"
        session.runtime_state.pause_count += 1
        
        self.repo.log_state_transition(session_id, old_status, "PAUSED")
        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="InterviewPaused",
            message="Session paused by operator.",
            payload={"pause_count": session.runtime_state.pause_count}
        )
        self.repo.commit()
        return session

    def resume_session(self, session_id: str) -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            raise NotFoundException("Session not found.")

        self.validate_transition(session.status, "RESUMED")
        
        # Auto restore to running status based on pointer history
        target_state = "QUESTION_RUNNING" if session.runtime_state.current_question_index > 0 else "ROUND_RUNNING"
        session.status = target_state
        
        self.repo.log_state_transition(session_id, "PAUSED", "RESUMED")
        self.repo.log_state_transition(session_id, "RESUMED", target_state)
        
        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="InterviewResumed",
            message=f"Session resumed back to {target_state}.",
            payload={"target_state": target_state}
        )
        self.repo.commit()
        return session

    def disconnect_session(self, session_id: str) -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            raise NotFoundException("Session not found.")

        if session.status in {"FINISHED", "CANCELLED", "FAILED"}:
            return session

        old_status = session.status
        session.status = "DISCONNECTED"
        session.runtime_state.connection_status = "DISCONNECTED"
        
        self.repo.log_state_transition(session_id, old_status, "DISCONNECTED")
        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="CandidateDisconnected",
            message="Active connection lost. Grace period timer initiated.",
            payload={"previous_state": old_status}
        )
        self.repo.commit()
        return session

    def reconnect_session(self, session_token: str, ip: Optional[str] = None, ua: Optional[str] = None) -> orm.InterviewSessionORM:
        session = self.repo.get_session_by_token(session_token)
        if not session or not session.runtime_state:
            raise NotFoundException("Invalid session token.")

        self.validate_transition(session.status, "RECOVERING")
        
        session.runtime_state.reconnect_attempts += 1
        session.runtime_state.connection_status = "CONNECTED"
        
        old_status = session.status
        session.status = "RECOVERING"
        
        self.repo.log_connection(str(session.id), "RECONNECTED", ip, ua)
        self.repo.log_state_transition(str(session.id), old_status, "RECOVERING")
        
        # Resume back to running loop state
        target_state = "QUESTION_RUNNING" if session.runtime_state.current_question_index > 0 else "ROUND_RUNNING"
        session.status = target_state
        self.repo.log_state_transition(str(session.id), "RECOVERING", target_state)
        
        self.repo.log_recovery(str(session.id), session.runtime_state.reconnect_attempts, True, 0)
        self.repo.log_runtime_event(
            session_id=str(session.id),
            event_type="CandidateReconnected",
            message="Candidate successfully reconnected and session was recovered.",
            payload={"target_state": target_state}
        )
        self.repo.commit()
        return session

    def terminate_session(self, session_id: str, verdict: str = "FINISHED") -> orm.InterviewSessionORM:
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            raise NotFoundException("Session not found.")

        self.validate_transition(session.status, verdict)
        
        old_status = session.status
        session.status = verdict
        session.ended_at = func.now()
        session.runtime_state.connection_status = "DISCONNECTED"

        self.repo.log_state_transition(session_id, old_status, verdict)
        self.repo.log_runtime_event(
            session_id=session_id,
            event_type="InterviewFinished" if verdict == "FINISHED" else "InterviewFailed",
            message=f"Session execution completed with verdict: {verdict}",
            payload={"score": session.runtime_state.current_score}
        )
        self.repo.commit()
        return session

    def record_timer_tick(self, session_id: str, elapsed_seconds: int):
        session = self.repo.get_session(session_id)
        if not session or not session.runtime_state:
            return

        state = session.runtime_state
        state.remaining_time_seconds = max(0, state.remaining_time_seconds - elapsed_seconds)

        # Periodic snapshot write
        self.repo.save_timer_snapshot(
            session_id=session_id,
            timer_name="session_timer",
            elapsed=elapsed_seconds,
            remaining=state.remaining_time_seconds
        )

        if state.remaining_time_seconds <= 0:
            # Terminate automatically on timeout
            self.terminate_session(session_id, "FAILED")
            self.repo.log_runtime_event(session_id, "SessionTimeout", "Interview terminated due to total duration timeout.", {})

        self.repo.commit()
