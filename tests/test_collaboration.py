# tests/test_collaboration.py
import pytest
import uuid

from app.adapter.db.collaboration_repo import CollaborationRepository
from app.domain.services.collaboration_service import CollaborationService
from app.adapter.db import orm


@pytest.fixture
def collab_service(db_session):
    repo = CollaborationRepository(db_session)
    return CollaborationService(repo)


def test_chat_message_flow(collab_service, db_session):
    session_id = str(uuid.uuid4())
    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_chat",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # 1. Send public chat message
    msg = collab_service.send_chat(
        session_id=session_id,
        sender_id="CANDIDATE",
        recipient_id=None,
        text="Hello world!"
    )
    assert msg.id is not None
    assert msg.sender_id == "CANDIDATE"
    assert msg.recipient_id is None
    assert msg.message_text == "Hello world!"

    # 2. Retrieve history
    history = collab_service.get_chats(session_id)
    assert len(history) == 1
    assert history[0].message_text == "Hello world!"


def test_whiteboard_event_flow(collab_service, db_session):
    session_id = str(uuid.uuid4())
    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_wb",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # Save stroke event
    wb = collab_service.save_canvas_stroke(
        session_id=session_id,
        event_type="DRAW_PATH",
        data='{"color":"#fff","points":[0,0,10,10]}'
    )
    assert wb.id is not None
    assert wb.event_type == "DRAW_PATH"
    assert wb.event_data == '{"color":"#fff","points":[0,0,10,10]}'

    # Get history
    history = collab_service.get_whiteboard(session_id)
    assert len(history) == 1
    assert history[0].event_type == "DRAW_PATH"


def test_uploaded_files_registry(collab_service, db_session):
    session_id = str(uuid.uuid4())
    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_files",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # Log file metadata
    fl = collab_service.upload_file_meta(
        session_id=session_id,
        uploader_id="RECRUITER",
        file_name="diagram.png",
        file_url="http://s3/diagram.png",
        size=1024,
        content_type="image/png"
    )
    assert fl.id is not None
    assert fl.file_name == "diagram.png"
    assert fl.file_url == "http://s3/diagram.png"

    # Fetch files
    files = collab_service.get_uploaded_files(session_id)
    assert len(files) == 1
    assert files[0].file_name == "diagram.png"


def test_live_notes_role_access_filtering(collab_service, db_session):
    session_id = str(uuid.uuid4())
    session_orm = orm.InterviewSessionORM(
        id=uuid.UUID(session_id),
        application_id=uuid.uuid4(),
        session_token="test_token_notes",
        status="PENDING"
    )
    db_session.add(session_orm)
    db_session.commit()

    # 1. Save recruiter private notes
    recruiter_note = collab_service.save_notes(
        session_id=session_id,
        role="RECRUITER",
        content="Candidate shows strong algorithmic base.",
        is_private=True
    )
    assert recruiter_note.id is not None
    assert recruiter_note.author_role == "RECRUITER"
    assert recruiter_note.is_private is True

    # 2. Save candidate public notes
    candidate_note = collab_service.save_notes(
        session_id=session_id,
        role="CANDIDATE",
        content="Shared diagram link.",
        is_private=False
    )
    assert candidate_note.id is not None
    assert candidate_note.author_role == "CANDIDATE"
    assert candidate_note.is_private is False

    # 3. Retrieve notes as Recruiter (should see BOTH)
    recruiter_notes = collab_service.get_notes(session_id, requesting_role="RECRUITER")
    assert len(recruiter_notes) == 2

    # 4. Retrieve notes as Candidate (should ONLY see candidate public note)
    candidate_notes = collab_service.get_notes(session_id, requesting_role="CANDIDATE")
    assert len(candidate_notes) == 1
    assert candidate_notes[0].author_role == "CANDIDATE"
