# services/interview-engine/app/adapter/db/execution_repo.py
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class ExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        application_id: str,
        interview_plan_id: str,
        session_token: str
    ) -> orm.InterviewSessionORM:
        session = orm.InterviewSessionORM(
            id=uuid.uuid4(),
            application_id=uuid.UUID(application_id),
            interview_plan_id=uuid.UUID(interview_plan_id),
            session_token=session_token,
            status="CREATED"
        )
        self.db.add(session)
        self.db.flush()

        runtime = orm.SessionRuntimeStateORM(
            id=uuid.uuid4(),
            interview_session_id=session.id,
            current_round_index=0,
            current_question_index=0,
            current_difficulty="MEDIUM",
            current_score=0.0,
            remaining_time_seconds=3600,
            connection_status="DISCONNECTED",
            warnings_count=0,
            pause_count=0,
            reconnect_attempts=0,
            adaptive_decisions=[]
        )
        self.db.add(runtime)
        self.db.flush()
        return session

    def get_session(self, session_id: str) -> Optional[orm.InterviewSessionORM]:
        try:
            session_uuid = uuid.UUID(session_id)
            return self.db.query(orm.InterviewSessionORM).filter(
                orm.InterviewSessionORM.id == session_uuid
            ).first()
        except ValueError:
            return None

    def get_session_by_token(self, token: str) -> Optional[orm.InterviewSessionORM]:
        return self.db.query(orm.InterviewSessionORM).filter(
            orm.InterviewSessionORM.session_token == token
        ).first()

    def log_state_transition(self, session_id: str, from_state: str, to_state: str):
        history = orm.StateHistoryORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            from_state=from_state,
            to_state=to_state
        )
        self.db.add(history)
        self.db.flush()

    def log_runtime_event(self, session_id: str, event_type: str, message: str, payload: dict):
        evt = orm.RuntimeEventORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            event_type=event_type,
            message=message,
            payload=payload
        )
        self.db.add(evt)
        self.db.flush()

    def save_timer_snapshot(self, session_id: str, timer_name: str, elapsed: int, remaining: int):
        session_uuid = uuid.UUID(session_id)
        snap = self.db.query(orm.TimerSnapshotORM).filter(
            orm.TimerSnapshotORM.interview_session_id == session_uuid,
            orm.TimerSnapshotORM.timer_name == timer_name
        ).first()

        if snap:
            snap.elapsed_seconds = elapsed
            snap.remaining_seconds = remaining
        else:
            snap = orm.TimerSnapshotORM(
                id=uuid.uuid4(),
                interview_session_id=session_uuid,
                timer_name=timer_name,
                elapsed_seconds=elapsed,
                remaining_seconds=remaining
            )
            self.db.add(snap)
        self.db.flush()

    def log_connection(self, session_id: str, event: str, ip: Optional[str], ua: Optional[str]):
        log = orm.ConnectionLogORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            event=event,
            ip_address=ip,
            user_agent=ua
        )
        self.db.add(log)
        self.db.flush()

    def log_recovery(self, session_id: str, attempt: int, success: bool, restored_elapsed: int):
        log = orm.RecoveryLogORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            attempt_number=attempt,
            success=success,
            restored_elapsed_seconds=restored_elapsed
        )
        self.db.add(log)
        self.db.flush()

    def commit(self):
        self.db.commit()
