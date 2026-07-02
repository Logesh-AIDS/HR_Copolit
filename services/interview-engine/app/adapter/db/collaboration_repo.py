# services/interview-engine/app/adapter/db/collaboration_repo.py
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class CollaborationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_chat_message(
        self,
        session_id: str,
        sender_id: str,
        recipient_id: Optional[str],
        text: str
    ) -> orm.CollaborationChatORM:
        chat = orm.CollaborationChatORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_text=text
        )
        self.db.add(chat)
        self.db.flush()
        return chat

    def get_chat_history(self, session_id: str) -> List[orm.CollaborationChatORM]:
        return self.db.query(orm.CollaborationChatORM).filter(
            orm.CollaborationChatORM.interview_session_id == uuid.UUID(session_id)
        ).order_by(orm.CollaborationChatORM.created_at.asc()).all()

    def save_whiteboard_event(
        self,
        session_id: str,
        event_type: str,
        data: str
    ) -> orm.CollaborationWhiteboardORM:
        wb = orm.CollaborationWhiteboardORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            event_type=event_type,
            event_data=data
        )
        self.db.add(wb)
        self.db.flush()
        return wb

    def get_whiteboard_events(self, session_id: str) -> List[orm.CollaborationWhiteboardORM]:
        return self.db.query(orm.CollaborationWhiteboardORM).filter(
            orm.CollaborationWhiteboardORM.interview_session_id == uuid.UUID(session_id)
        ).order_by(orm.CollaborationWhiteboardORM.created_at.asc()).all()

    def save_file(
        self,
        session_id: str,
        uploader_id: str,
        file_name: str,
        file_url: str,
        size: int,
        content_type: str
    ) -> orm.CollaborationFileORM:
        fl = orm.CollaborationFileORM(
            id=uuid.uuid4(),
            interview_session_id=uuid.UUID(session_id),
            uploader_id=uploader_id,
            file_name=file_name,
            file_url=file_url,
            file_size_bytes=size,
            content_type=content_type
        )
        self.db.add(fl)
        self.db.flush()
        return fl

    def get_files(self, session_id: str) -> List[orm.CollaborationFileORM]:
        return self.db.query(orm.CollaborationFileORM).filter(
            orm.CollaborationFileORM.interview_session_id == uuid.UUID(session_id)
        ).order_by(orm.CollaborationFileORM.created_at.asc()).all()

    def save_notes(
        self,
        session_id: str,
        role: str,
        content: str,
        is_private: bool
    ) -> orm.CollaborationNoteORM:
        sess_uuid = uuid.UUID(session_id)
        
        # Check if notes record already exists for role (we auto-update notes as they type)
        note = self.db.query(orm.CollaborationNoteORM).filter(
            orm.CollaborationNoteORM.interview_session_id == sess_uuid,
            orm.CollaborationNoteORM.author_role == role
        ).first()

        if note:
            note.notes_content = content
            note.is_private = is_private
            note.updated_at = datetime.now(timezone.utc)
        else:
            note = orm.CollaborationNoteORM(
                id=uuid.uuid4(),
                interview_session_id=sess_uuid,
                author_role=role,
                notes_content=content,
                is_private=is_private
            )
            self.db.add(note)
        self.db.flush()
        return note

    def get_notes(self, session_id: str, requesting_role: str) -> List[orm.CollaborationNoteORM]:
        sess_uuid = uuid.UUID(session_id)
        # Recruiter role can see both private recruiter notes and candidate notes
        # Candidate role can only see public notes
        query = self.db.query(orm.CollaborationNoteORM).filter(
            orm.CollaborationNoteORM.interview_session_id == sess_uuid
        )
        if requesting_role != "RECRUITER":
            query = query.filter(orm.CollaborationNoteORM.is_private == False)
        return query.all()

    def commit(self):
        self.db.commit()
