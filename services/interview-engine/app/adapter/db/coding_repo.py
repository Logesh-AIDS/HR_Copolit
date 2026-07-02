# services/interview-engine/app/adapter/db/coding_repo.py
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class CodingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_coding_problem(
        self,
        title: str,
        statement: str,
        time_limit_ms: int = 2000,
        memory_limit_bytes: int = 268435456,
        reference_solution: Optional[str] = None
    ) -> orm.CodingProblemORM:
        p = orm.CodingProblemORM(
            id=uuid.uuid4(),
            title=title,
            statement=statement,
            time_limit_ms=time_limit_ms,
            memory_limit_bytes=memory_limit_bytes,
            reference_solution=reference_solution
        )
        self.db.add(p)
        self.db.flush()
        return p

    def get_coding_problem(self, problem_id: str) -> Optional[orm.CodingProblemORM]:
        try:
            p_uuid = uuid.UUID(problem_id)
            return self.db.query(orm.CodingProblemORM).filter(orm.CodingProblemORM.id == p_uuid).first()
        except ValueError:
            return None

    def create_test_case(
        self,
        problem_id: str,
        input_data: str,
        expected_output: str,
        is_hidden: bool = False
    ) -> orm.CodingTestCaseORM:
        tc = orm.CodingTestCaseORM(
            id=uuid.uuid4(),
            problem_id=uuid.UUID(problem_id),
            input=input_data,
            expected_output=expected_output,
            is_hidden=is_hidden
        )
        self.db.add(tc)
        self.db.flush()
        return tc

    def get_test_cases(self, problem_id: str) -> List[orm.CodingTestCaseORM]:
        try:
            p_uuid = uuid.UUID(problem_id)
            return self.db.query(orm.CodingTestCaseORM).filter(orm.CodingTestCaseORM.problem_id == p_uuid).all()
        except ValueError:
            return []

    def get_or_create_question_attempt(
        self,
        session_id: str,
        question_id: str
    ) -> orm.QuestionAttemptORM:
        sess_uuid = uuid.UUID(session_id)
        quest_uuid = uuid.UUID(question_id)
        
        attempt = self.db.query(orm.QuestionAttemptORM).filter(
            orm.QuestionAttemptORM.session_id == sess_uuid,
            orm.QuestionAttemptORM.question_id == quest_uuid
        ).first()
        
        if not attempt:
            attempt = orm.QuestionAttemptORM(
                id=uuid.uuid4(),
                session_id=sess_uuid,
                question_id=quest_uuid,
                time_spent_seconds=0
            )
            self.db.add(attempt)
            self.db.flush()
            
        return attempt

    def create_submission(
        self,
        attempt_id: str,
        source_code: str,
        language: str,
        test_cases_passed: int,
        total_test_cases: int,
        execution_time_ms: Optional[float] = None,
        memory_used_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
        submission_id: Optional[str] = None
    ) -> orm.CodeSubmissionORM:
        sub_uuid = uuid.UUID(submission_id) if submission_id else uuid.uuid4()
        sub = orm.CodeSubmissionORM(
            id=sub_uuid,
            question_attempt_id=uuid.UUID(attempt_id),
            source_code=source_code,
            language=language,
            test_cases_passed=test_cases_passed,
            total_test_cases=total_test_cases,
            execution_time_ms=execution_time_ms,
            memory_used_bytes=memory_used_bytes,
            error_message=error_message
        )
        self.db.add(sub)
        self.db.flush()
        return sub

    def get_submissions_by_attempt(self, attempt_id: str) -> List[orm.CodeSubmissionORM]:
        try:
            att_uuid = uuid.UUID(attempt_id)
            return self.db.query(orm.CodeSubmissionORM).filter(orm.CodeSubmissionORM.question_attempt_id == att_uuid).all()
        except ValueError:
            return []

    def get_submission(self, submission_id: str) -> Optional[orm.CodeSubmissionORM]:
        try:
            sub_uuid = uuid.UUID(submission_id)
            return self.db.query(orm.CodeSubmissionORM).filter(orm.CodeSubmissionORM.id == sub_uuid).first()
        except ValueError:
            return None

    def log_compilation(
        self,
        submission_id: str,
        logs: str,
        success: bool
    ) -> orm.CompilationLogORM:
        cl = orm.CompilationLogORM(
            id=uuid.uuid4(),
            submission_id=uuid.UUID(submission_id),
            logs=logs,
            success=success
        )
        self.db.add(cl)
        self.db.flush()
        return cl

    def log_execution(
        self,
        submission_id: str,
        test_case_id: Optional[str],
        status: str,
        actual_output: Optional[str],
        execution_time_ms: Optional[int],
        memory_used_bytes: Optional[int]
    ) -> orm.ExecutionResultORM:
        tc_uuid = uuid.UUID(test_case_id) if test_case_id else None
        er = orm.ExecutionResultORM(
            id=uuid.uuid4(),
            submission_id=uuid.UUID(submission_id),
            test_case_id=tc_uuid,
            status=status,
            actual_output=actual_output,
            execution_time_ms=execution_time_ms,
            memory_used_bytes=memory_used_bytes
        )
        self.db.add(er)
        self.db.flush()
        return er

    def commit(self):
        self.db.commit()
