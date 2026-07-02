# tests/test_webrtc.py
import pytest
import uuid

from app.adapter.db.webrtc_repo import WebRTCRepository
from app.domain.services.webrtc_service import WebRTCService
from app.adapter.db import orm


@pytest.fixture
def webrtc_service(db_session):
    repo = WebRTCRepository(db_session)
    return WebRTCService(repo)


def test_create_and_join_webrtc_room(webrtc_service, db_session):
    session_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    # Seed parents to satisfy Foreign Key constraints!
    user = orm.UserORM(
        id=user_id,
        email="candidate_rtc@test.com",
        password_hash="pw_hash",
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    candidate = orm.CandidateORM(
        id=uuid.uuid4(),
        user_id=user.id,
        first_name="Jane",
        last_name="Smith",
        email="candidate_rtc@test.com",
        resume_url="s3://resumes/resume.pdf"
    )
    db_session.add(candidate)
    db_session.flush()

    recruiter = orm.RecruiterORM(
        id=uuid.uuid4(),
        user_id=user.id,
        email="recruiter_rtc@test.com",
        company_name="Tech Corp",
        password_hash="pw_hash"
    )
    db_session.add(recruiter)
    db_session.flush()

    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # 1. Create Room
    room = webrtc_service.create_room(session_id)
    assert room is not None
    assert room.status == "ACTIVE"

    # 2. Join Room (Candidate peer)
    room = webrtc_service.join_room(session_id, peer_id="CANDIDATE")
    assert len(room.connections) == 1
    assert room.connections[0].peer_id == "CANDIDATE"
    assert room.connections[0].connection_state == "CONNECTING"

    # 3. Join Room (Recruiter peer)
    room = webrtc_service.join_room(session_id, peer_id="RECRUITER")
    assert len(room.connections) == 2
    assert any(c.peer_id == "RECRUITER" for c in room.connections)


def test_webrtc_connection_statistics_logging(webrtc_service, db_session):
    session_id = str(uuid.uuid4())
    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_stats",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # Report Stats
    conn = webrtc_service.report_stats(
        session_id=session_id,
        peer_id="CANDIDATE",
        state="CONNECTED",
        packet_loss=0.02,
        latency_ms=45,
        jitter_ms=1.5
    )

    assert conn is not None
    assert conn.peer_id == "CANDIDATE"
    assert conn.connection_state == "CONNECTED"
    assert conn.packet_loss == 0.02
    assert conn.latency_ms == 45
    assert conn.jitter_ms == 1.5

    # Retrieve Stats
    stats = webrtc_service.fetch_stats(session_id)
    assert len(stats) == 1
    assert stats[0]["peer_id"] == "CANDIDATE"
    assert stats[0]["packet_loss"] == 0.02


def test_webrtc_event_logging(webrtc_service, db_session):
    session_id = str(uuid.uuid4())
    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_events",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # Create Room
    webrtc_service.create_room(session_id)

    # Log SDP Offer Event
    webrtc_service.log_event(
        session_id=session_id,
        peer_id="CANDIDATE",
        event_type="SDP_OFFER",
        details="Generated WebRTC SDP offer payload."
    )

    # Retrieve and verify from db
    room = webrtc_service.repo.get_room_by_session(session_id)
    assert room is not None
    db_session.refresh(room)
    assert len(room.events) >= 2  # includes RoomCreated + SDP_OFFER
    assert any(e.event_type == "SDP_OFFER" for e in room.events)
