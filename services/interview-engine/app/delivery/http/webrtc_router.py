# services/interview-engine/app/delivery/http/webrtc_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.webrtc_repo import WebRTCRepository
from app.domain.services.webrtc_service import WebRTCService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webrtc", tags=["Real-Time WebRTC Communication"])

def get_webrtc_service(db: Session = Depends(get_db)) -> WebRTCService:
    repo = WebRTCRepository(db)
    return WebRTCService(repo)


class PeerRequestPayload(BaseModel):
    peer_id: str = Field(..., description="Unique identifier for the peer candidate/recruiter")


class StatsReportPayload(BaseModel):
    peer_id: str = Field(..., description="Peer reporting stats")
    state: str = Field(..., description="Active connection state (connected, disconnected, failed)")
    packet_loss: float = Field(0.0, description="WebRTC packet loss percentage")
    latency_ms: int = Field(0, description="Round trip time latency in milliseconds")
    jitter_ms: float = Field(0.0, description="RTC Jitter in milliseconds")


@router.post("/rooms/create/{session_id}", status_code=status.HTTP_201_CREATED)
def create_room(
    session_id: str,
    service: WebRTCService = Depends(get_webrtc_service)
):
    """
    Creates a secure WebRTC signaling room associated with an active interview session.
    """
    try:
        room = service.create_room(session_id)
        return make_success_response({
            "room_id": str(room.id),
            "session_id": str(room.interview_session_id),
            "status": room.status
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rooms/join/{session_id}")
def join_room(
    session_id: str,
    payload: PeerRequestPayload,
    service: WebRTCService = Depends(get_webrtc_service)
):
    """
    Authorizes and registers a peer entering the signaling room.
    """
    try:
        room = service.join_room(session_id, payload.peer_id)
        return make_success_response({
            "room_id": str(room.id),
            "peer_id": payload.peer_id,
            "status": "JOINED"
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rooms/leave/{session_id}")
def leave_room(
    session_id: str,
    payload: PeerRequestPayload,
    service: WebRTCService = Depends(get_webrtc_service)
):
    """
    Unregisters a peer leaving the signaling room.
    """
    try:
        room = service.leave_room(session_id, payload.peer_id)
        return make_success_response({
            "room_id": str(room.id),
            "peer_id": payload.peer_id,
            "status": "LEFT"
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stats/report/{session_id}")
def report_stats(
    session_id: str,
    payload: StatsReportPayload,
    service: WebRTCService = Depends(get_webrtc_service)
):
    """
    Submits real-time WebRTC packet logs, round-trip latencies, and jitters.
    """
    try:
        conn = service.report_stats(
            session_id=session_id,
            peer_id=payload.peer_id,
            state=payload.state,
            packet_loss=payload.packet_loss,
            latency_ms=payload.latency_ms,
            jitter_ms=payload.jitter_ms
        )
        return make_success_response({
            "connection_id": str(conn.id),
            "peer_id": conn.peer_id,
            "state": conn.connection_state
        })
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/report/{session_id}")
def fetch_stats(
    session_id: str,
    service: WebRTCService = Depends(get_webrtc_service)
):
    """
    Retrieves current active peer stats details and connections.
    """
    try:
        stats = service.fetch_stats(session_id)
        return make_success_response(stats)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e))
