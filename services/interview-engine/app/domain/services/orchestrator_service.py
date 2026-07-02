# services/interview-engine/app/domain/services/orchestrator_service.py
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.interview_repo import InterviewRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class OrchestratorService:
    """
    Business logic layer governing the dynamic generation, execution, and adaptation of interviews.
    """
    def __init__(self, repo: InterviewRepository):
        self.repo = repo

    def generate_interview_blueprint(
        self,
        candidate_id: str,
        job_id: str,
        company_config: dict,
        recruiter_preferences: dict
    ) -> orm.InterviewPlanORM:
        db = self.repo.db

        # 1. Fetch Candidate and Job references directly from PostgreSQL
        cand_uuid = uuid.UUID(candidate_id)
        job_uuid = uuid.UUID(job_id)

        # Attempt to find candidate profile first to obtain user_id
        candidate_profile = db.query(orm.CandidateORM).filter(orm.CandidateORM.id == cand_uuid).first()
        if candidate_profile:
            candidate = db.query(orm.CandidateIntelligenceORM).filter(
                orm.CandidateIntelligenceORM.user_id == candidate_profile.user_id
            ).first()
        else:
            candidate = db.query(orm.CandidateIntelligenceORM).filter(
                orm.CandidateIntelligenceORM.user_id == cand_uuid
            ).first()

        job = db.query(orm.JobIntelligenceORM).filter(
            orm.JobIntelligenceORM.job_id == job_uuid
        ).first()

        # Fail-safe fallbacks if profiles aren't parsed/generated yet
        cand_level = candidate.career_level if candidate else "MID"
        cand_focus = candidate.career_focus if candidate else "General"
        job_title = job.title if job else "Software Engineer"
        job_seniority = job.expected_seniority if job else "MID"

        # Determine difficulty JUNIOR -> EASY, MID -> MEDIUM, SENIOR -> HARD
        base_difficulty = recruiter_preferences.get("difficulty")
        if not base_difficulty:
            if job_seniority == "SENIOR" or cand_level == "SENIOR":
                base_difficulty = "HARD"
            elif job_seniority == "JUNIOR" or cand_level == "JUNIOR":
                base_difficulty = "EASY"
            else:
                base_difficulty = "MEDIUM"

        # 2. Build Rounds Definitions dynamically
        rounds = []
        rationales = []

        # MCQ / General Round
        rounds.append({
            "name": "General Technical MCQ",
            "objective": "Verify baseline technical knowledge.",
            "category": "MCQ",
            "difficulty": base_difficulty,
            "expected_skills": ["Python", "General Software Engineering"],
            "max_time_minutes": 15,
            "question_count": 5,
            "evaluation_strategy": "Automatic score grading.",
            "success_criteria": "Score >= 60%",
            "failure_criteria": "Score < 40%"
        })
        rationales.append("Added General Technical MCQ round as standard baseline.")

        # Coding / Algorithm Round
        rounds.append({
            "name": "Coding challenges",
            "objective": "Assess programming depth and algorithmic logic.",
            "category": "CODING",
            "difficulty": base_difficulty,
            "expected_skills": ["Data Structures", "Algorithms"],
            "max_time_minutes": 25,
            "question_count": 3,
            "evaluation_strategy": "Testcase compilation outputs verification.",
            "success_criteria": "All testcases pass.",
            "failure_criteria": "Compilation failures or timeout."
        })
        rationales.append("Added Coding challenges round to evaluate algorithmic problem-solving.")

        # Machine Learning / AI Round if applicable
        has_ml = False
        if job:
            has_ml = any(sk.category in {"MACHINE_LEARNING", "DEEP_LEARNING"} for sk in job.skills)
        if candidate and cand_focus == "Machine Learning Engineering":
            has_ml = True

        if has_ml:
            rounds.append({
                "name": "Machine Learning Core Concepts",
                "objective": "Verify ML systems and modeling capabilities.",
                "category": "MACHINE_LEARNING",
                "difficulty": base_difficulty,
                "expected_skills": ["PyTorch", "Model Evaluation"],
                "max_time_minutes": 15,
                "question_count": 4,
                "evaluation_strategy": "Model parameter discussions and design choice scoring.",
                "success_criteria": "Score >= 70%",
                "failure_criteria": "Lack of core model comprehension."
            })
            rationales.append("Added Machine Learning Core Concepts round because AI/ML required skills were detected.")

        # SQL / Database Round
        has_db = False
        if job:
            has_db = any(sk.category == "DATABASE" for sk in job.skills)
        if has_db:
            rounds.append({
                "name": "SQL & Schema Design",
                "objective": "Verify relational query optimization capabilities.",
                "category": "SQL",
                "difficulty": base_difficulty,
                "expected_skills": ["PostgreSQL", "Query Tuning"],
                "max_time_minutes": 15,
                "question_count": 3,
                "evaluation_strategy": "Query execution syntax and cost analysis.",
                "success_criteria": "Queries produce correct joins.",
                "failure_criteria": "Invalid joins or suboptimal indexing."
            })
            rationales.append("Added SQL & Schema Design round because database required skills were detected.")

        # System Design Round (for Mid/Senior candidates)
        if cand_level in {"MID", "SENIOR"} or job_seniority in {"MID", "SENIOR"}:
            rounds.append({
                "name": "System Design & Architecture",
                "objective": "Verify distributed system scaling and message queue patterns.",
                "category": "SYSTEM_DESIGN",
                "difficulty": base_difficulty,
                "expected_skills": ["Orchestration", "Caching", "Microservices"],
                "max_time_minutes": 20,
                "question_count": 2,
                "evaluation_strategy": "Architectural tradeoffs discussions.",
                "success_criteria": "High scalability tradeoffs explained.",
                "failure_criteria": "Suboptimal data replication patterns proposed."
            })
            rationales.append(f"Added System Design & Architecture round because candidate level is {cand_level}.")

        # Behavioral / HR Round
        rounds.append({
            "name": "Behavioral Competency",
            "objective": "Assess leadership values, communication, and conflict resolution.",
            "category": "BEHAVIORAL",
            "difficulty": base_difficulty,
            "expected_skills": ["Leadership", "Communication"],
            "max_time_minutes": 15,
            "question_count": 3,
            "evaluation_strategy": "STAR method validation scoring.",
            "success_criteria": "Positive alignment with values.",
            "failure_criteria": "Poor communication or ethics flags."
        })
        rationales.append("Added Behavioral Competency round to verify organizational cultural fit.")

        # Calculate durations
        total_dur = sum(r["max_time_minutes"] for r in rounds)
        passing_score = company_config.get("passing_score", 60.0)

        # 3. Create plan
        plan = self.repo.create_interview_plan(
            candidate_id=candidate_id,
            job_id=job_id,
            candidate_level=cand_level,
            role=job_title,
            difficulty=base_difficulty,
            total_duration_minutes=total_dur,
            passing_criteria=passing_score
        )
        self.repo.commit()

        # Save blueprints & definitions
        blueprint_name = f"Adaptive Blueprint for {job_title}"
        rules = {
            "termination_rules": "Terminate immediately on plagiarism flags, system timeouts, or cumulative score drops.",
            "adaptive_rules": "Scoring below 40% reduces difficulty; scoring above 85% increases difficulty.",
            "retry_rules": "Allow 1 question retry in coding blocks on environment runtime failure.",
            "break_rules": "Allow 3-minute break between technical rounds."
        }
        self.repo.save_blueprint(
            plan_id=str(plan.id),
            blueprint_name=blueprint_name,
            rounds_data=rounds,
            rules=rules
        )

        # Create execution state
        self.repo.create_execution_state(
            plan_id=str(plan.id),
            remaining_time_seconds=total_dur * 60
        )

        # Log decision histories
        for rat in rationales:
            self.repo.log_decision(str(plan.id), "ROUND_SELECTION", rat)

        self.repo.log_timeline(
            plan_id=str(plan.id),
            event_type="INTERVIEW_PLANNED",
            message=f"Generated blueprint: {blueprint_name} containing {len(rounds)} rounds."
        )

        logger.info(
            f"[EVENT: InterviewPlanned] Plan ID: {plan.id}, Candidate: {candidate_id}, "
            f"Job: {job_id}, Rounds: {len(rounds)}, Duration: {total_dur} mins"
        )

        return plan

    def start_interview(self, plan_id: str) -> orm.InterviewPlanORM:
        plan = self.repo.get_interview_plan(plan_id)
        if not plan:
            raise NotFoundException("Target interview plan not found.")

        plan.status = "ACTIVE"
        plan.execution_state.connection_status = "CONNECTED"
        self.repo.commit()

        first_round = plan.blueprint.rounds[0] if plan.blueprint.rounds else None
        round_name = first_round.name if first_round else "General"
        
        self.repo.log_timeline(
            plan_id=plan_id,
            event_type="ROUND_STARTED",
            message=f"Round 1: {round_name} started."
        )

        return plan

    def pause_interview(self, plan_id: str) -> orm.InterviewPlanORM:
        plan = self.repo.get_interview_plan(plan_id)
        if not plan or not plan.execution_state:
            raise NotFoundException("Target interview plan not found.")

        plan.execution_state.is_paused = True
        self.repo.commit()

        self.repo.log_timeline(
            plan_id=plan_id,
            event_type="INTERVIEW_PAUSED",
            message="Interview session paused."
        )

        return plan

    def resume_interview(self, plan_id: str) -> orm.InterviewPlanORM:
        plan = self.repo.get_interview_plan(plan_id)
        if not plan or not plan.execution_state:
            raise NotFoundException("Target interview plan not found.")

        plan.execution_state.is_paused = False
        plan.execution_state.connection_status = "CONNECTED"
        self.repo.commit()

        self.repo.log_timeline(
            plan_id=plan_id,
            event_type="INTERVIEW_RESUMED",
            message="Interview session resumed."
        )

        return plan

    def submit_answer_and_adapt(
        self,
        plan_id: str,
        question_score: float,
        skipped: bool = False,
        warning_message: Optional[str] = None
    ) -> orm.InterviewPlanORM:
        plan = self.repo.get_interview_plan(plan_id)
        if not plan or not plan.execution_state or not plan.blueprint:
            raise NotFoundException("Target interview plan not found.")

        state = plan.execution_state

        if warning_message:
            # Append warning message safely
            current_warn = list(state.warnings)
            current_warn.append(warning_message)
            state.warnings = current_warn

        if skipped:
            current_skipped = list(state.skipped_questions)
            current_skipped.append(f"Q_{state.current_round_index}_{state.current_question_index}")
            state.skipped_questions = current_skipped
            self.repo.log_timeline(plan_id, "QUESTION_SKIPPED", f"Question index {state.current_question_index} was skipped by candidate.")

        # Update scoring total
        state.score = round(state.score + question_score, 2)
        state.current_question_index += 1

        # Fetch round definition details
        rounds_list = sorted(plan.blueprint.rounds, key=lambda r: r.round_index)
        current_round_def = rounds_list[state.current_round_index] if state.current_round_index < len(rounds_list) else None

        if current_round_def:
            # 1. Apply Adaptive Difficulty settings based on scoring thresholds
            # Threshold evaluate triggers after 3 questions in a round block
            if state.current_question_index >= 3:
                avg_score = (state.score / (state.current_question_index * 10.0)) * 100.0
                
                # Check for poor performance (Score < 40%) -> Reduce difficulty
                if avg_score < 40.0 and current_round_def.difficulty == "HARD":
                    current_round_def.difficulty = "MEDIUM"
                    self.repo.log_adaptive_decision(
                        plan_id=plan_id,
                        round_index=state.current_round_index,
                        trigger_event=f"Question score drop. Average round score: {avg_score:.1f}%",
                        adjustment_details="Reduced round difficulty from HARD to MEDIUM."
                    )
                    self.repo.log_timeline(
                        plan_id=plan_id,
                        event_type="DIFFICULTY_CHANGED",
                        message=f"Orchestrator reduced Round {state.current_round_index + 1} difficulty to MEDIUM."
                    )

                # Check for excellent performance (Score > 85%) -> Increase difficulty
                elif avg_score > 85.0 and current_round_def.difficulty == "MEDIUM":
                    current_round_def.difficulty = "HARD"
                    self.repo.log_adaptive_decision(
                        plan_id=plan_id,
                        round_index=state.current_round_index,
                        trigger_event=f"High score performance. Average round score: {avg_score:.1f}%",
                        adjustment_details="Increased round difficulty from MEDIUM to HARD."
                    )
                    self.repo.log_timeline(
                        plan_id=plan_id,
                        event_type="DIFFICULTY_CHANGED",
                        message=f"Orchestrator increased Round {state.current_round_index + 1} difficulty to HARD."
                    )

            # Check if current round has reached its questions count limits
            if state.current_question_index >= current_round_def.question_count:
                # Transition to next round block
                state.current_question_index = 0
                state.current_round_index += 1
                
                self.repo.log_timeline(
                    plan_id=plan_id,
                    event_type="ROUND_FINISHED",
                    message=f"Round {state.current_round_index} ({current_round_def.name}) completed."
                )

                if state.current_round_index >= len(rounds_list):
                    # Out of rounds -> Complete interview
                    state.is_completed = True
                    plan.status = "COMPLETED"
                    self.repo.log_timeline(plan_id, "INTERVIEW_COMPLETED", "Candidate completed all blueprint rounds.")
                else:
                    next_round = rounds_list[state.current_round_index]
                    self.repo.log_timeline(plan_id, "ROUND_STARTED", f"Round {state.current_round_index + 1}: {next_round.name} started.")

        self.repo.commit()
        return plan

    def finish_interview(self, plan_id: str) -> orm.InterviewPlanORM:
        plan = self.repo.get_interview_plan(plan_id)
        if not plan or not plan.execution_state:
            raise NotFoundException("Target interview plan not found.")

        state = plan.execution_state
        state.is_completed = True
        plan.status = "COMPLETED"

        # Verify passing criteria
        max_possible = len(plan.blueprint.rounds) * 50.0  # assume 5 questions per round, 10 pts each
        pct = (state.score / max_possible) * 100.0 if max_possible > 0 else 0.0

        if pct < plan.passing_criteria:
            state.is_failed = True
            plan.status = "FAILED"
            self.repo.log_timeline(plan_id, "INTERVIEW_FAILED", f"Interview failed. Candidate scored {pct:.1f}% (required {plan.passing_criteria}%).")
        else:
            self.repo.log_timeline(plan_id, "INTERVIEW_COMPLETED", f"Candidate passed the interview scoring {pct:.1f}%.")

        self.repo.commit()
        return plan
