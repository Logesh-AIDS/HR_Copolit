# services/interview-engine/app/domain/services/webrtc_service.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from services.common.exceptions import NotFoundException, ValidationException
from app.adapter.db.webrtc_repo import WebRTCRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class WebRTCService:
    """
    Business layer managing signaling rooms registrations, connection quality stats processing,
    and WebRTC negotiation event trails auditing.
    """
    def __init__(self, repo: WebRTCRepository):
        self.repo = repo

    def create_room(self, session_id: str) -> orm.WebRTCRoomORM:
        room = self.repo.create_room(session_id)
        self.repo.log_webrtc_event(
            room_id=str(room.id),
            peer_id=None,
            event_type="RoomCreated",
            details=f"Signaling room initialized for session: {session_id}"
        )
        self.repo.commit()
        return room

    def join_room(self, session_id: str, peer_id: str) -> orm.WebRTCRoomORM:
        room = self.repo.get_room_by_session(session_id)
        if not room:
            room = self.repo.create_room(session_id)

        self.repo.save_connection_stats(
            room_id=str(room.id),
            peer_id=peer_id,
            state="CONNECTING",
            packet_loss=0.0,
            latency=0,
            jitter=0.0
        )
        self.repo.log_webrtc_event(
            room_id=str(room.id),
            peer_id=peer_id,
            event_type="PeerJoined",
            details=f"Peer: {peer_id} entered signaling room."
        )
        self.repo.commit()
        return room

    def leave_room(self, session_id: str, peer_id: str) -> orm.WebRTCRoomORM:
        room = self.repo.get_room_by_session(session_id)
        if not room:
            raise NotFoundException("Active signaling room not found.")

        self.repo.save_connection_stats(
            room_id=str(room.id),
            peer_id=peer_id,
            state="DISCONNECTED",
            packet_loss=0.0,
            latency_ms=0,
            jitter_ms=0.0
        )
        self.repo.log_webrtc_event(
            room_id=str(room.id),
            peer_id=peer_id,
            event_type="PeerLeft",
            details=f"Peer: {peer_id} exited signaling room."
        )
        self.repo.commit()
        return room

    def report_stats(
        self,
        session_id: str,
        peer_id: str,
        state: str,
        packet_loss: float,
        latency_ms: int,
        jitter_ms: float
    ) -> orm.WebRTCConnectionORM:
        room = self.repo.get_room_by_session(session_id)
        if not room:
            room = self.repo.create_room(session_id)

        conn = self.repo.save_connection_stats(
            room_id=str(room.id),
            peer_id=peer_id,
            state=state,
            packet_loss=packet_loss,
            latency=latency_ms,
            jitter=jitter_ms
        )
        self.repo.commit()
        return conn

    def log_event(self, session_id: str, peer_id: Optional[str], event_type: str, details: Optional[str]):
        room = self.repo.get_room_by_session(session_id)
        if not room:
            room = self.repo.create_room(session_id)

        self.repo.log_webrtc_event(
            room_id=str(room.id),
            peer_id=peer_id,
            event_type=event_type,
            details=details
        )
        self.repo.commit()

    def fetch_stats(self, session_id: str) -> List[dict]:
        room = self.repo.get_room_by_session(session_id)
        if not room:
            return []

        return [
            {
                "peer_id": c.peer_id,
                "connection_state": c.connection_state,
                "packet_loss": c.packet_loss,
                "latency_ms": c.latency_ms,
                "jitter_ms": c.jitter_ms,
                "updated_at": c.updated_at
            } for c in room.connections
        ]
