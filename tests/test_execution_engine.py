# tests/test_execution_engine.py
import pytest
import uuid

from app.adapter.db.execution_repo import ExecutionRepository
from app.adapter.db.interview_repo import InterviewRepository
from app.domain.services.execution_service import ExecutionService
from app.domain.services.orchestrator_service import OrchestratorService
from services.common.exceptions import ValidationException
from app.adapter.db import orm


@pytest.fixture
def execution_service(db_session):
    repo = ExecutionRepository(db_session)
    plan_repo = InterviewRepository(db_session)
    return ExecutionService(repo, plan_repo)


@pytest.fixture
def orchestrator_service(db_session):
    repo = InterviewRepository(db_session)
    return OrchestratorService(repo)


def test_session_creation_and_state_initialization(execution_service, orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Seed parent data
    user = orm.UserORM(
        id=user_id,
        email="candidate_exec@test.com",
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
        email="candidate_exec@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter_exec@test.com",
        company_name="AI Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(
        id=uuid.UUID(job_id),
        recruiter_id=recruiter.id,
        title="Software Engineer",
        description="Systems design",
        experience_level="MID"
    )
    db_session.add(job)
    db_session.flush()

    # Generate plan
    plan = orchestrator_service.generate_interview_blueprint(
        candidate_id=candidate_id,
        job_id=job_id,
        company_config={"passing_score": 60.0},
        recruiter_preferences={}
    )

    # Seed application
    application = orm.ApplicationORM(
        id=uuid.uuid4(),
        candidate_id=candidate.id,
        job_id=job.id,
        status="APPLIED"
    )
    db_session.add(application)
    db_session.flush()

    # Create Session
    session = execution_service.create_session(
        application_id=str(application.id),
        plan_id=str(plan.id)
    )

    assert session is not None
    assert session.status == "CREATED"
    assert session.session_token.startswith("sess_")
    assert session.runtime_state is not None
    assert session.runtime_state.current_round_index == 0
    assert session.runtime_state.connection_status == "DISCONNECTED"

    # Assert event timeline
    events = db_session.query(orm.RuntimeEventORM).filter(
        orm.RuntimeEventORM.interview_session_id == session.id
    ).all()
    assert len(events) == 1
    assert events[0].event_type == "InterviewInitialized"


def test_state_machine_transition_validations(execution_service, orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Seed parent data
    user = orm.UserORM(id=user_id, email="cand_sm@test.com", password_hash="pw_hash", is_verified=True)
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(id=uuid.UUID(candidate_id), user_id=user.id, first_name="A", last_name="B", email="cand_sm@test.com", resume_url="s3://url")
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(id=uuid.uuid4(), user_id=user.id, email="rec_sm@test.com", company_name="C", password_hash="pw_hash")
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(id=uuid.UUID(job_id), recruiter_id=recruiter.id, title="E", description="D", experience_level="MID")
    db_session.add(job)
    db_session.flush()

    plan = orchestrator_service.generate_interview_blueprint(candidate_id, job_id, {}, {})
    application = orm.ApplicationORM(id=uuid.uuid4(), candidate_id=candidate.id, job_id=job.id)
    db_session.add(application)
    db_session.flush()

    session = execution_service.create_session(str(application.id), str(plan.id))

    # Reject invalid transition CREATED -> QUESTION_RUNNING
    with pytest.raises(ValidationException):
        execution_service.start_question(str(session.id), 0)

    # Allowed transition CREATED -> STARTED
    session = execution_service.start_session(str(session.id))
    assert session.status == "STARTED"

    # Allowed transition STARTED -> ROUND_RUNNING
    session = execution_service.start_round(str(session.id), round_index=0)
    assert session.status == "ROUND_RUNNING"

    # Allowed transition ROUND_RUNNING -> QUESTION_RUNNING
    session = execution_service.start_question(str(session.id), question_index=0)
    assert session.status == "QUESTION_RUNNING"

    # Reject invalid transition QUESTION_RUNNING -> STARTED
    with pytest.raises(ValidationException):
        execution_service.start_session(str(session.id))


def test_pause_and_resume_session(execution_service, orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Seed parents
    user = orm.UserORM(id=user_id, email="cand_pr@test.com", password_hash="pw", is_verified=True)
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(id=uuid.UUID(candidate_id), user_id=user.id, first_name="A", last_name="B", email="cand_pr@test.com", resume_url="s3://url")
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(id=uuid.uuid4(), user_id=user.id, email="rec_pr@test.com", company_name="C", password_hash="pw")
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(id=uuid.UUID(job_id), recruiter_id=recruiter.id, title="E", description="D", experience_level="MID")
    db_session.add(job)
    db_session.flush()

    plan = orchestrator_service.generate_interview_blueprint(candidate_id, job_id, {}, {})
    application = orm.ApplicationORM(id=uuid.uuid4(), candidate_id=candidate.id, job_id=job.id)
    db_session.add(application)
    db_session.flush()

    session = execution_service.create_session(str(application.id), str(plan.id))
    session = execution_service.start_session(str(session.id))

    # Pause
    session = execution_service.pause_session(str(session.id))
    assert session.status == "PAUSED"
    assert session.runtime_state.pause_count == 1

    # Resume back to running
    session = execution_service.resume_session(str(session.id))
    assert session.status == "ROUND_RUNNING"


def test_disconnect_and_recovery_flow(execution_service, orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    user = orm.UserORM(id=user_id, email="cand_rec@test.com", password_hash="pw", is_verified=True)
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(id=uuid.UUID(candidate_id), user_id=user.id, first_name="A", last_name="B", email="cand_rec@test.com", resume_url="s3://url")
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(id=uuid.uuid4(), user_id=user.id, email="rec_rec@test.com", company_name="C", password_hash="pw")
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(id=uuid.UUID(job_id), recruiter_id=recruiter.id, title="E", description="D", experience_level="MID")
    db_session.add(job)
    db_session.flush()

    plan = orchestrator_service.generate_interview_blueprint(candidate_id, job_id, {}, {})
    application = orm.ApplicationORM(id=uuid.uuid4(), candidate_id=candidate.id, job_id=job.id)
    db_session.add(application)
    db_session.flush()

    session = execution_service.create_session(str(application.id), str(plan.id))
    session = execution_service.start_session(str(session.id))

    # Disconnect socket
    session = execution_service.disconnect_session(str(session.id))
    assert session.status == "DISCONNECTED"
    assert session.runtime_state.connection_status == "DISCONNECTED"

    # Reconnect via token
    session = execution_service.reconnect_session(
        session_token=session.session_token,
        ip="127.0.0.1",
        ua="Mozilla/5.0"
    )
    assert session.status == "ROUND_RUNNING"
    assert session.runtime_state.connection_status == "CONNECTED"
    assert session.runtime_state.reconnect_attempts == 1


def test_execution_timers_and_timeout(execution_service, orchestrator_service, db_session):
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    user = orm.UserORM(id=user_id, email="cand_time@test.com", password_hash="pw", is_verified=True)
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(id=uuid.UUID(candidate_id), user_id=user.id, first_name="A", last_name="B", email="cand_time@test.com", resume_url="s3://url")
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(id=uuid.uuid4(), user_id=user.id, email="rec_time@test.com", company_name="C", password_hash="pw")
    db_session.add(recruiter)
    db_session.flush()

    job = orm.JobORM(id=uuid.UUID(job_id), recruiter_id=recruiter.id, title="E", description="D", experience_level="MID")
    db_session.add(job)
    db_session.flush()

    plan = orchestrator_service.generate_interview_blueprint(candidate_id, job_id, {}, {})
    application = orm.ApplicationORM(id=uuid.uuid4(), candidate_id=candidate.id, job_id=job.id)
    db_session.add(application)
    db_session.flush()

    session = execution_service.create_session(str(application.id), str(plan.id))
    session = execution_service.start_session(str(session.id))

    init_remaining = session.runtime_state.remaining_time_seconds

    # Ticking clock deduction
    execution_service.record_timer_tick(str(session.id), elapsed_seconds=30)
    assert session.runtime_state.remaining_time_seconds == init_remaining - 30

    # Ensure snapshot was updated
    snap = db_session.query(orm.TimerSnapshotORM).filter(
        orm.TimerSnapshotORM.interview_session_id == session.id,
        orm.TimerSnapshotORM.timer_name == "session_timer"
    ).first()
    assert snap is not None
    assert snap.remaining_seconds == init_remaining - 30

    # Ticking clock past limits -> timeout fail
    execution_service.record_timer_tick(str(session.id), elapsed_seconds=init_remaining)
    assert session.status == "FAILED"
