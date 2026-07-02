# services/interview-engine/app/adapter/db/interview_repo.py
import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class InterviewRepository(SQLAlchemyRepository):
    """
    Handles database operations for interview plans, blueprints, execution states, timelines, and decision logs.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def get_interview_plan(self, plan_id: str) -> Optional[orm.InterviewPlanORM]:
        try:
            plan_uuid = uuid.UUID(plan_id)
        except ValueError:
            return None
        return self.db.query(orm.InterviewPlanORM).filter(
            orm.InterviewPlanORM.id == plan_uuid
        ).first()

    def create_interview_plan(
        self,
        candidate_id: str,
        job_id: str,
        candidate_level: str,
        role: str,
        difficulty: str,
        total_duration_minutes: int = 60,
        passing_criteria: float = 60.0
    ) -> orm.InterviewPlanORM:
        plan = orm.InterviewPlanORM(
            candidate_id=uuid.UUID(candidate_id),
            job_id=uuid.UUID(job_id),
            candidate_level=candidate_level,
            role=role,
            difficulty=difficulty,
            total_duration_minutes=total_duration_minutes,
            passing_criteria=passing_criteria,
            status="PLANNED"
        )
        return self.add(plan)

    def save_blueprint(
        self,
        plan_id: str,
        blueprint_name: str,
        rounds_data: List[dict],
        rules: dict
    ) -> orm.InterviewBlueprintORM:
        plan = self.get_interview_plan(plan_id)
        if not plan:
            raise ValueError("Target interview plan not found.")

        # Clear old blueprint if existing
        if plan.blueprint:
            self.db.delete(plan.blueprint)

        bp = orm.InterviewBlueprintORM(
            interview_plan_id=plan.id,
            name=blueprint_name,
            rounds_count=len(rounds_data),
            termination_rules=rules.get("termination_rules"),
            adaptive_rules=rules.get("adaptive_rules"),
            retry_rules=rules.get("retry_rules"),
            break_rules=rules.get("break_rules")
        )
        self.db.add(bp)
        self.db.flush()

        for idx, round_data in enumerate(rounds_data):
            rd = orm.RoundDefinitionORM(
                interview_blueprint_id=bp.id,
                round_index=idx,
                name=round_data["name"],
                objective=round_data.get("objective"),
                category=round_data["category"],
                difficulty=round_data["difficulty"],
                expected_skills=round_data.get("expected_skills", []),
                max_time_minutes=round_data.get("max_time_minutes", 15),
                question_count=round_data.get("question_count", 5),
                evaluation_strategy=round_data.get("evaluation_strategy"),
                success_criteria=round_data.get("success_criteria"),
                failure_criteria=round_data.get("failure_criteria")
            )
            bp.rounds.append(rd)

        self.db.commit()
        return bp

    def create_execution_state(
        self,
        plan_id: str,
        remaining_time_seconds: int = 3600
    ) -> orm.InterviewExecutionStateORM:
        plan = self.get_interview_plan(plan_id)
        if not plan:
            raise ValueError("Target interview plan not found.")

        if plan.execution_state:
            self.db.delete(plan.execution_state)

        state = orm.InterviewExecutionStateORM(
            interview_plan_id=plan.id,
            current_round_index=0,
            current_question_index=0,
            remaining_time_seconds=remaining_time_seconds,
            score=0.0,
            connection_status="DISCONNECTED",
            is_paused=False,
            is_completed=False,
            is_failed=False
        )
        return self.add(state)

    def log_timeline(self, plan_id: str, event_type: str, message: str) -> orm.InterviewTimelineORM:
        timeline = orm.InterviewTimelineORM(
            interview_plan_id=uuid.UUID(plan_id),
            event_type=event_type.upper(),
            message=message
        )
        return self.add(timeline)

    def log_decision(self, plan_id: str, decision_type: str, rationale: str) -> orm.DecisionHistoryORM:
        dh = orm.DecisionHistoryORM(
            interview_plan_id=uuid.UUID(plan_id),
            decision_type=decision_type.upper(),
            rationale=rationale
        )
        return self.add(dh)

    def log_adaptive_decision(
        self,
        plan_id: str,
        round_index: int,
        trigger_event: str,
        adjustment_details: str
    ) -> orm.AdaptiveDecisionORM:
        ad = orm.AdaptiveDecisionORM(
            interview_plan_id=uuid.UUID(plan_id),
            round_index=round_index,
            trigger_event=trigger_event,
            adjustment_details=adjustment_details
        )
        return self.add(ad)
