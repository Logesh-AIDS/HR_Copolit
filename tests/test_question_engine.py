# tests/test_question_engine.py
import pytest
import uuid

from app.adapter.db.question_repo import QuestionRepository
from app.adapter.vector.question_qdrant_repo import QuestionQdrantRepository
from app.domain.services.question_service import QuestionService
from app.adapter.db import orm


@pytest.fixture
def question_service(db_session):
    repo = QuestionRepository(db_session)
    vector_repo = QuestionQdrantRepository()
    return QuestionService(repo, vector_repo)


def test_add_and_get_question(question_service, db_session):
    q = question_service.add_question(
        category="Programming",
        subcategory="OOP",
        difficulty="MID",
        statement="Explain class inheritance mechanisms in C++.",
        required_skills=["C++", "OOP"],
        hints=["What is virtual table?", "Explain virtual destructors."]
    )
    assert q.id is not None
    assert q.category == "Programming"
    assert q.difficulty == "MID"
    
    # Retrieve question
    fetched = question_service.repo.get_question(str(q.id))
    assert fetched is not None
    assert fetched.problem_statement == "Explain class inheritance mechanisms in C++."


def test_search_questions(question_service, db_session):
    question_service.add_question(
        category="Algorithms",
        subcategory="Trees",
        difficulty="SENIOR",
        statement="Balance a Red-Black tree insertion.",
        required_skills=["Trees", "C++"],
        hints=[]
    )
    question_service.add_question(
        category="Behavioral",
        subcategory="Leadership",
        difficulty="MID",
        statement="Describe a conflict resolution strategy.",
        required_skills=["Communication"],
        hints=[]
    )

    results = question_service.search_questions(category="Algorithms", difficulty="SENIOR")
    assert len(results) == 1
    assert "Red-Black" in results[0].problem_statement


def test_adaptive_difficulty_tuning(question_service, db_session):
    session_id = str(uuid.uuid4())
    
    # Register mock plan
    plan_orm = orm.InterviewPlanORM(
        id=uuid.UUID(session_id),
        candidate_id=uuid.uuid4(),
        job_id=uuid.uuid4()
    )
    db_session.add(plan_orm)
    db_session.commit()

    # 1. Scale down on low score
    diff = question_service.adapt_difficulty(
        session_id=session_id,
        current_difficulty="SENIOR",
        previous_score=3.0
    )
    assert diff == "MID"

    # Verify decision logged
    decisions = db_session.query(orm.AdaptiveDecisionORM).filter(
        orm.AdaptiveDecisionORM.interview_plan_id == uuid.UUID(session_id)
    ).all()
    assert len(decisions) == 1
    assert "MID" in decisions[0].adjustment_details

    # 2. Scale up on high score
    diff = question_service.adapt_difficulty(
        session_id=session_id,
        current_difficulty="MID",
        previous_score=9.0
    )
    assert diff == "SENIOR"


def test_get_next_question_flow(question_service, db_session):
    session_id = str(uuid.uuid4())
    
    # Register mock session
    sess_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_qnext",
        status="PENDING"
    )
    db_session.add(sess_orm)
    db_session.commit()

    # Seed some questions
    q1 = question_service.add_question(
        category="Programming",
        subcategory="Go",
        difficulty="JUNIOR",
        statement="Explain Go channels.",
        required_skills=["Go"],
        hints=[]
    )
    
    q_next = question_service.get_next_question(
        session_id=session_id,
        skills=["Go"],
        category="Programming",
        difficulty="JUNIOR"
    )
    assert q_next.id == q1.id
    
    # Verify retrieval log was created
    logs = db_session.query(orm.QuestionRetrievalLogORM).filter(
        orm.QuestionRetrievalLogORM.interview_session_id == uuid.UUID(session_id)
    ).all()
    assert len(logs) == 1
    assert logs[0].question_id == q1.id
