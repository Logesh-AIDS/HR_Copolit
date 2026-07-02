# services/interview-engine/app/delivery/http/collaboration_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.collaboration_repo import CollaborationRepository
from app.domain.services.collaboration_service import CollaborationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collaboration", tags=["Live Interview Collaboration"])

def get_collab_service(db: Session = Depends(get_db)) -> CollaborationService:
    repo = CollaborationRepository(db)
    return CollaborationService(repo)


class ChatSendPayload(BaseModel):
    sender_id: str = Field(..., description="Sender identification")
    recipient_id: Optional[str] = Field(None, description="Private target peer")
    message_text: str = Field(..., description="Message string")


class WhiteboardSavePayload(BaseModel):
    event_type: str = Field(..., description="Canvas stroke actions (e.g. DRAW_PATH, CLEAR)")
    event_data: str = Field(..., description="Stringified stroke coordinates color and brush values")


class FileUploadPayload(BaseModel):
    uploader_id: str = Field(..., description="Uploader identification")
    file_name: str = Field(..., description="Original file name")
    file_url: str = Field(..., description="File storage path")
    file_size_bytes: int = Field(..., description="Size in bytes")
    content_type: str = Field(..., description="Document type")


class NotesSavePayload(BaseModel):
    role: str = Field(..., description="Author role (RECRUITER, CANDIDATE)")
    content: str = Field(..., description="Note text content")
    is_private: bool = Field(True, description="Private note configuration")


@router.post("/chat/{session_id}", status_code=status.HTTP_201_CREATED)
def send_chat(
    session_id: str,
    payload: ChatSendPayload,
    service: CollaborationService = Depends(get_collab_service)
):
    try:
        chat = service.send_chat(
            session_id=session_id,
            sender_id=payload.sender_id,
            recipient_id=payload.recipient_id,
            text=payload.message_text
        )
        return make_success_response({
            "message_id": str(chat.id),
            "sender_id": chat.sender_id,
            "recipient_id": chat.recipient_id,
            "created_at": chat.created_at.isoformat()
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/{session_id}")
def get_chats(
    session_id: str,
    service: CollaborationService = Depends(get_collab_service)
):
    chats = service.get_chats(session_id)
    return make_success_response([
        {
            "id": str(c.id),
            "sender_id": c.sender_id,
            "recipient_id": c.recipient_id,
            "message_text": c.message_text,
            "created_at": c.created_at.isoformat()
        } for c in chats
    ])


@router.post("/whiteboard/{session_id}", status_code=status.HTTP_201_CREATED)
def save_whiteboard(
    session_id: str,
    payload: WhiteboardSavePayload,
    service: CollaborationService = Depends(get_collab_service)
):
    try:
        wb = service.save_canvas_stroke(
            session_id=session_id,
            event_type=payload.event_type,
            data=payload.event_data
        )
        return make_success_response({
            "event_id": str(wb.id),
            "event_type": wb.event_type,
            "created_at": wb.created_at.isoformat()
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/whiteboard/{session_id}")
def get_whiteboard(
    session_id: str,
    service: CollaborationService = Depends(get_collab_service)
):
    strokes = service.get_whiteboard(session_id)
    return make_success_response([
        {
            "id": str(s.id),
            "event_type": s.event_type,
            "event_data": s.event_data,
            "created_at": s.created_at.isoformat()
        } for s in strokes
    ])


@router.post("/files/{session_id}", status_code=status.HTTP_201_CREATED)
def save_file(
    session_id: str,
    payload: FileUploadPayload,
    service: CollaborationService = Depends(get_collab_service)
):
    try:
        fl = service.upload_file_meta(
            session_id=session_id,
            uploader_id=payload.uploader_id,
            file_name=payload.file_name,
            file_url=payload.file_url,
            size=payload.file_size_bytes,
            content_type=payload.content_type
        )
        return make_success_response({
            "file_id": str(fl.id),
            "file_name": fl.file_name,
            "file_url": fl.file_url
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{session_id}")
def get_files(
    session_id: str,
    service: CollaborationService = Depends(get_collab_service)
):
    files = service.get_uploaded_files(session_id)
    return make_success_response([
        {
            "id": str(f.id),
            "uploader_id": f.uploader_id,
            "file_name": f.file_name,
            "file_url": f.file_url,
            "file_size_bytes": f.file_size_bytes,
            "content_type": f.content_type,
            "created_at": f.created_at.isoformat()
        } for f in files
    ])


@router.post("/notes/{session_id}")
def save_notes(
    session_id: str,
    payload: NotesSavePayload,
    service: CollaborationService = Depends(get_collab_service)
):
    try:
        note = service.save_notes(
            session_id=session_id,
            role=payload.role,
            content=payload.content,
            is_private=payload.is_private
        )
        return make_success_response({
            "note_id": str(note.id),
            "author_role": note.author_role,
            "is_private": note.is_private,
            "updated_at": note.updated_at.isoformat()
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notes/{session_id}")
def get_notes(
    session_id: str,
    requesting_role: str = Query("CANDIDATE", description="Role requesting notes context"),
    service: CollaborationService = Depends(get_collab_service)
):
    try:
        notes = service.get_notes(session_id, requesting_role)
        return make_success_response([
            {
                "id": str(n.id),
                "author_role": n.author_role,
                "notes_content": n.notes_content,
                "is_private": n.is_private,
                "updated_at": n.updated_at.isoformat()
            } for n in notes
        ])
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))
