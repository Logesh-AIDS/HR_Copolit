# services/interview-engine/app/domain/services/collaboration_service.py
import logging
from typing import List, Optional, Dict, Any

from services.common.exceptions import ValidationException, NotFoundException
from app.adapter.db.collaboration_repo import CollaborationRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class CollaborationService:
    def __init__(self, repo: CollaborationRepository):
        self.repo = repo

    def send_chat(
        self,
        session_id: str,
        sender_id: str,
        recipient_id: Optional[str],
        text: str
    ) -> orm.CollaborationChatORM:
        if not text or not text.strip():
            raise ValidationException("Message text cannot be empty.")
        
        chat = self.repo.save_chat_message(session_id, sender_id, recipient_id, text)
        self.repo.commit()
        return chat

    def get_chats(self, session_id: str) -> List[orm.CollaborationChatORM]:
        return self.repo.get_chat_history(session_id)

    def save_canvas_stroke(self, session_id: str, event_type: str, data: str) -> orm.CollaborationWhiteboardORM:
        if not event_type or not data:
            raise ValidationException("Event type and data payload are required.")
        
        wb = self.repo.save_whiteboard_event(session_id, event_type, data)
        self.repo.commit()
        return wb

    def get_whiteboard(self, session_id: str) -> List[orm.CollaborationWhiteboardORM]:
        return self.repo.get_whiteboard_events(session_id)

    def upload_file_meta(
        self,
        session_id: str,
        uploader_id: str,
        file_name: str,
        file_url: str,
        size: int,
        content_type: str
    ) -> orm.CollaborationFileORM:
        if not file_name or not file_url:
            raise ValidationException("File name and URL target are required.")
        if size <= 0:
            raise ValidationException("File size must be greater than zero.")
        
        fl = self.repo.save_file(session_id, uploader_id, file_name, file_url, size, content_type)
        self.repo.commit()
        return fl

    def get_uploaded_files(self, session_id: str) -> List[orm.CollaborationFileORM]:
        return self.repo.get_files(session_id)

    def save_notes(self, session_id: str, role: str, content: str, is_private: bool) -> orm.CollaborationNoteORM:
        if role not in {"RECRUITER", "CANDIDATE"}:
            raise ValidationException("Invalid author role classification.")
        if content is None:
            content = ""

        note = self.repo.save_notes(session_id, role, content, is_private)
        self.repo.commit()
        return note

    def get_notes(self, session_id: str, requesting_role: str) -> List[orm.CollaborationNoteORM]:
        return self.repo.get_notes(session_id, requesting_role)
