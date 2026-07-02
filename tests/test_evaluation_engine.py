# tests/test_evaluation_engine.py
import pytest
import uuid

from app.adapter.db.evaluation_repo import EvaluationRepository
from app.domain.services.evaluation_service import EvaluationService
from app.adapter.db import orm


@pytest.fixture
def evaluation_service(db_session):
    repo = EvaluationRepository(db_session)
    return EvaluationService(repo)


def test_evaluate_answer_flow(evaluation_service, db_session):
    session_id = str(uuid.uuid4())
    question_id = str(uuid.uuid4())

    # Seed active session
    plan_orm = orm.InterviewPlanORM(
        id=uuid.UUID(session_id),
        candidate_id=uuid.uuid4(),
        job_id=uuid.uuid4()
    )
    db_session.add(plan_orm)
    
    sess_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_eval",
        status="PENDING"
    )
    db_session.add(sess_orm)
    
    # Seed question
    q_orm = orm.QuestionORM(
        id=uuid.UUID(question_id),
        category="Programming",
        subcategory="System Design",
        difficulty="MEDIUM",
        problem_statement="Explain REST protocol and statelessness."
    )
    db_session.add(q_orm)
    db_session.commit()

    # Evaluate
    ev = evaluation_service.evaluate_answer(
        session_id=session_id,
        question_id=question_id,
        candidate_answer="REST is stateless, caches responses, reduces latency, and supports scale tradeoffs."
    )
    assert ev.id is not None
    assert ev.overall_score > 0.0

    # Get report
    rep = evaluation_service.get_report(str(ev.id))
    assert rep["evaluation_id"] == str(ev.id)
    assert len(rep["concepts_coverage"]) > 0
    assert rep["similarity"]["cosine_similarity"] > 0.0

    # Re-evaluate
    re_ev = evaluation_service.re_evaluate_answer(
        eval_id=str(ev.id),
        role="RECRUITER",
        new_score=9.5,
        reason="Excellent explanation of stateless cache constraints."
    )
    assert re_ev.overall_score == 9.5

    # Check score history
    rep_updated = evaluation_service.get_report(str(ev.id))
    assert len(rep_updated["score_history"]) == 1
    assert rep_updated["score_history"][0]["changer_role"] == "RECRUITER"
