# tests/test_orchestrator.py
import pytest
import uuid

from app.adapter.db.interview_repo import InterviewRepository
from app.domain.services.orchestrator_service import OrchestratorService
from app.adapter.db import orm


@pytest.fixture
def orchestrator_service(db_session):
    repo = InterviewRepository(db_session)
    return OrchestratorService(repo)


def test_dynamic_blueprint_planning_fresher(orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Create parent User and Recruiter first to satisfy FKs!
    user = orm.UserORM(
        id=user_id,
        email="candidate@test.com",
        password_hash="pw_hash",
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(
        id=uuid.UUID(candidate_id),
        user_id=user.id,
        first_name="John",
        last_name="Doe",
        email="candidate@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter@test.com",
        company_name="Tech Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(
        id=uuid.UUID(job_id),
        recruiter_id=recruiter.id,
        title="Junior Developer",
        description="Python backend",
        experience_level="JUNIOR"
    )
    db_session.add(job)
    db_session.flush()

    doc = orm.DocumentORM(
        id=uuid.uuid4(),
        user_id=user.id,
        name="resume.pdf",
        document_type="RESUME"
    )
    db_session.add(doc)
    db_session.flush()

    pr = orm.ParsedResumeORM(
        id=uuid.uuid4(),
        document_id=doc.id,
        user_id=user.id,
        status="COMPLETED"
    )
    db_session.add(pr)
    db_session.flush()

    # Seed Candidate profile: JUNIOR level
    cand_intel = orm.CandidateIntelligenceORM(
        id=uuid.uuid4(),
        parsed_resume_id=pr.id,
        user_id=user.id,
        document_id=doc.id,
        career_level="JUNIOR",
        career_focus="Backend Software Engineering"
    )
    db_session.add(cand_intel)

    # Seed Job description intelligence
    job_intel = orm.JobIntelligenceORM(
        id=uuid.uuid4(),
        job_id=job.id,
        title="Junior Developer",
        experience_years_required=1,
        expected_seniority="JUNIOR"
    )
    db_session.add(job_intel)
    db_session.commit()

    # Generate plan
    plan = orchestrator_service.generate_interview_blueprint(
        candidate_id=candidate_id,
        job_id=job_id,
        company_config={"passing_score": 50.0},
        recruiter_preferences={}
    )

    assert plan is not None
    assert plan.candidate_level == "JUNIOR"
    assert plan.difficulty == "EASY"  # Mapped from Junior expected seniority
    assert plan.status == "PLANNED"
    assert plan.passing_criteria == 50.0

    # Ensure rounds list does NOT contain ML or System Design
    categories = {r.category for r in plan.blueprint.rounds}
    assert "MCQ" in categories
    assert "CODING" in categories
    assert "BEHAVIORAL" in categories
    assert "MACHINE_LEARNING" not in categories
    assert "SYSTEM_DESIGN" not in categories

    # Assert decision history log exists
    decisions = db_session.query(orm.DecisionHistoryORM).filter(
        orm.DecisionHistoryORM.interview_plan_id == plan.id
    ).all()
    assert len(decisions) > 0


def test_dynamic_blueprint_planning_senior_ml(orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Create parent User and Recruiter first to satisfy FKs!
    user = orm.UserORM(
        id=user_id,
        email="candidate_sr@test.com",
        password_hash="pw_hash",
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(
        id=uuid.UUID(candidate_id),
        user_id=user.id,
        first_name="Jane",
        last_name="Smith",
        email="candidate_sr@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter_sr@test.com",
        company_name="AI Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(
        id=uuid.UUID(job_id),
        recruiter_id=recruiter.id,
        title="Lead Machine Learning Engineer",
        description="PyTorch models design",
        experience_level="SENIOR"
    )
    db_session.add(job)
    db_session.flush()

    doc = orm.DocumentORM(
        id=uuid.uuid4(),
        user_id=user.id,
        name="resume.pdf",
        document_type="RESUME"
    )
    db_session.add(doc)
    db_session.flush()

    pr = orm.ParsedResumeORM(
        id=uuid.uuid4(),
        document_id=doc.id,
        user_id=user.id,
        status="COMPLETED"
    )
    db_session.add(pr)
    db_session.flush()

    # Seed Candidate profile: SENIOR level, ML focus
    cand_intel = orm.CandidateIntelligenceORM(
        id=uuid.uuid4(),
        parsed_resume_id=pr.id,
        user_id=user.id,
        document_id=doc.id,
        career_level="SENIOR",
        career_focus="Machine Learning Engineering"
    )
    db_session.add(cand_intel)

    # Seed Job description: SENIOR, has ML required skill
    job_intel = orm.JobIntelligenceORM(
        id=uuid.uuid4(),
        job_id=job.id,
        title="Lead Machine Learning Engineer",
        experience_years_required=6,
        expected_seniority="SENIOR"
    )
    db_session.add(job_intel)
    db_session.flush()

    skill_ml = orm.JobRequiredSkillORM(
        id=uuid.uuid4(),
        job_intelligence_id=job_intel.id,
        name="PyTorch",
        category="MACHINE_LEARNING",
        is_mandatory=True
    )
    db_session.add(skill_ml)
    db_session.commit()

    # Generate plan
    plan = orchestrator_service.generate_interview_blueprint(
        candidate_id=candidate_id,
        job_id=job_id,
        company_config={"passing_score": 70.0},
        recruiter_preferences={}
    )

    assert plan is not None
    assert plan.candidate_level == "SENIOR"
    assert plan.difficulty == "HARD"  # Mapped from Senior expected seniority

    # Ensure rounds list contains ML and System Design (since it's a senior ML engineer)
    categories = {r.category for r in plan.blueprint.rounds}
    assert "MCQ" in categories
    assert "CODING" in categories
    assert "MACHINE_LEARNING" in categories
    assert "SYSTEM_DESIGN" in categories
    assert "BEHAVIORAL" in categories


def test_adaptive_difficulty_reduction(orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Create dummy candidate and job records to satisfy foreign keys
    user = orm.UserORM(
        id=user_id,
        email="candidate_adapt_red@test.com",
        password_hash="pw_hash",
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(
        id=uuid.UUID(candidate_id),
        user_id=user.id,
        first_name="Jane",
        last_name="Smith",
        email="candidate_adapt_red@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter_adapt_red@test.com",
        company_name="AI Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(
        id=uuid.UUID(job_id),
        recruiter_id=recruiter.id,
        title="Lead Machine Learning Engineer",
        description="PyTorch models design",
        experience_level="SENIOR"
    )
    db_session.add(job)
    db_session.flush()

    # Generate plan
    plan = orchestrator_service.generate_interview_blueprint(
        candidate_id=candidate_id,
        job_id=job_id,
        company_config={"passing_score": 60.0},
        recruiter_preferences={"difficulty": "HARD"}
    )

    # Start
    orchestrator_service.start_interview(str(plan.id))

    # Submit 3 poor answers in the first round (which starts as HARD)
    # Total possible score for 3 questions at 10 pts each is 30.
    # Score 1.0 per question -> 3.0 out of 30.0 = 10% average score (< 40%)
    plan = orchestrator_service.submit_answer_and_adapt(str(plan.id), question_score=1.0)
    plan = orchestrator_service.submit_answer_and_adapt(str(plan.id), question_score=1.0)
    plan = orchestrator_service.submit_answer_and_adapt(str(plan.id), question_score=1.0)

    # Ensure current round difficulty adapts and drops from HARD to MEDIUM
    rounds_list = sorted(plan.blueprint.rounds, key=lambda r: r.round_index)
    first_round = rounds_list[0]
    assert first_round.difficulty == "MEDIUM"

    # Confirm adaptive decision log was created
    logs = db_session.query(orm.AdaptiveDecisionORM).filter(
        orm.AdaptiveDecisionORM.interview_plan_id == plan.id
    ).all()
    assert len(logs) > 0


def test_adaptive_difficulty_escalation(orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Create dummy candidate and job records to satisfy foreign keys
    user = orm.UserORM(
        id=user_id,
        email="candidate_adapt_esc@test.com",
        password_hash="pw_hash",
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(
        id=uuid.UUID(candidate_id),
        user_id=user.id,
        first_name="Jane",
        last_name="Smith",
        email="candidate_adapt_esc@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter_adapt_esc@test.com",
        company_name="AI Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(
        id=uuid.UUID(job_id),
        recruiter_id=recruiter.id,
        title="Lead Machine Learning Engineer",
        description="PyTorch models design",
        experience_level="SENIOR"
    )
    db_session.add(job)
    db_session.flush()

    # Generate plan
    plan = orchestrator_service.generate_interview_blueprint(
        candidate_id=candidate_id,
        job_id=job_id,
        company_config={"passing_score": 60.0},
        recruiter_preferences={"difficulty": "MEDIUM"}
    )

    # Start
    orchestrator_service.start_interview(str(plan.id))

    # Submit 3 high-performance answers (Score 9.0 per question -> 27.0 out of 30.0 = 90% average score (> 85%))
    plan = orchestrator_service.submit_answer_and_adapt(str(plan.id), question_score=9.0)
    plan = orchestrator_service.submit_answer_and_adapt(str(plan.id), question_score=9.0)
    plan = orchestrator_service.submit_answer_and_adapt(str(plan.id), question_score=9.0)

    # Ensure current round difficulty increases from MEDIUM to HARD
    rounds_list = sorted(plan.blueprint.rounds, key=lambda r: r.round_index)
    first_round = rounds_list[0]
    assert first_round.difficulty == "HARD"


def test_interview_execution_lifecycle_states(orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Create dummy candidate and job records to satisfy foreign keys
    user = orm.UserORM(
        id=user_id,
        email="candidate_lifecycle@test.com",
        password_hash="pw_hash",
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(
        id=uuid.UUID(candidate_id),
        user_id=user.id,
        first_name="Jane",
        last_name="Smith",
        email="candidate_lifecycle@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter_lifecycle@test.com",
        company_name="AI Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(
        id=uuid.UUID(job_id),
        recruiter_id=recruiter.id,
        title="Lead Machine Learning Engineer",
        description="PyTorch models design",
        experience_level="SENIOR"
    )
    db_session.add(job)
    db_session.flush()

    # Generate plan
    plan = orchestrator_service.generate_interview_blueprint(
        candidate_id=candidate_id,
        job_id=job_id,
        company_config={"passing_score": 60.0},
        recruiter_preferences={"difficulty": "MEDIUM"}
    )

    # 1. Start
    plan = orchestrator_service.start_interview(str(plan.id))
    assert plan.status == "ACTIVE"
    assert plan.execution_state.connection_status == "CONNECTED"

    # 2. Pause
    plan = orchestrator_service.pause_interview(str(plan.id))
    assert plan.execution_state.is_paused is True

    # 3. Resume
    plan = orchestrator_service.resume_interview(str(plan.id))
    assert plan.execution_state.is_paused is False
    assert plan.execution_state.connection_status == "CONNECTED"

    # 4. Finish
    plan = orchestrator_service.finish_interview(str(plan.id))
    assert plan.execution_state.is_completed is True
    # Initial score is 0.0 -> under passing criteria (60%) -> FAILED status
    assert plan.status == "FAILED"
