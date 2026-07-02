# tests/test_coding_engine.py
import pytest
import uuid

from app.adapter.db.coding_repo import CodingRepository
from app.domain.services.coding_service import CodingService
from app.adapter.db import orm


@pytest.fixture
def coding_service(db_session):
    repo = CodingRepository(db_session)
    return CodingService(repo)


def test_create_and_get_coding_problem(coding_service, db_session):
    prob = coding_service.repo.create_coding_problem(
        title="Sum Challenge",
        statement="Calculate a + b",
        time_limit_ms=1000,
        memory_limit_bytes=64 * 1024 * 1024,
        reference_solution="def solution(a, b): return a + b"
    )
    assert prob.id is not None
    assert prob.title == "Sum Challenge"
    
    # Create test case
    tc = coding_service.repo.create_test_case(
        problem_id=str(prob.id),
        input_data="1 2",
        expected_output="3",
        is_hidden=False
    )
    assert tc.id is not None
    assert tc.expected_output == "3"

    # Fetch
    fetched = coding_service.repo.get_coding_problem(str(prob.id))
    assert fetched is not None
    assert fetched.title == "Sum Challenge"


def test_code_run_sandbox_flow(coding_service):
    res = coding_service.run_code(
        code="def solution(n):\n    return n * 2",
        language="python",
        input_val="5"
    )
    assert "output" in res
    assert res["compilation_error"] is None


def test_code_submit_evaluation_flow(coding_service, db_session):
    session_id = str(uuid.uuid4())
    
    # Setup interview structures
    plan_orm = orm.InterviewPlanORM(
        id=uuid.UUID(session_id),
        candidate_id=uuid.uuid4(),
        job_id=uuid.uuid4()
    )
    db_session.add(plan_orm)
    
    sess_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_coding",
        status="PENDING"
    )
    db_session.add(sess_orm)
    db_session.commit()

    # Seed problem
    prob = coding_service.repo.create_coding_problem(
        title="Multiply",
        statement="Double input.",
        reference_solution="def solution(n): return n * 2"
    )
    # Seed 2 test cases
    coding_service.repo.create_test_case(str(prob.id), "5", "10", is_hidden=False)
    coding_service.repo.create_test_case(str(prob.id), "6", "12", is_hidden=True)
    db_session.commit()

    # Submit code
    sub = coding_service.submit_code(
        session_id=session_id,
        question_id=str(prob.id),
        code="def solution(n):\n    return n * 2",
        language="python"
    )
    assert sub.id is not None
    assert sub.language == "python"
    assert sub.total_test_cases == 2

    # Verify execution report
    rep = coding_service.get_report(str(sub.id))
    assert rep["submission_id"] == str(sub.id)
    assert len(rep["test_cases"]) == 2
