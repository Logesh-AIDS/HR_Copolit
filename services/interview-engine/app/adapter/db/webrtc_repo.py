# services/interview-engine/app/adapter/db/webrtc_repo.py
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class WebRTCRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_room(self, session_id: str) -> orm.WebRTCRoomORM:
        sess_uuid = uuid.UUID(session_id)
        
        # Check if active room already exists
        room = self.db.query(orm.WebRTCRoomORM).filter(
            orm.WebRTCRoomORM.interview_session_id == sess_uuid,
            orm.WebRTCRoomORM.status == "ACTIVE"
        ).first()
        if room:
            return room

        room = orm.WebRTCRoomORM(
            id=uuid.uuid4(),
            interview_session_id=sess_uuid,
            status="ACTIVE"
        )
        self.db.add(room)
        self.db.flush()
        return room

    def get_room(self, room_id: str) -> Optional[orm.WebRTCRoomORM]:
        try:
            room_uuid = uuid.UUID(room_id)
            return self.db.query(orm.WebRTCRoomORM).filter(
                orm.WebRTCRoomORM.id == room_uuid
            ).first()
        except ValueError:
            return None

    def get_room_by_session(self, session_id: str) -> Optional[orm.WebRTCRoomORM]:
        try:
            sess_uuid = uuid.UUID(session_id)
            return self.db.query(orm.WebRTCRoomORM).filter(
                orm.WebRTCRoomORM.interview_session_id == sess_uuid,
                orm.WebRTCRoomORM.status == "ACTIVE"
            ).first()
        except ValueError:
            return None

    def save_connection_stats(
        self,
        room_id: str,
        peer_id: str,
        state: str,
        packet_loss: float,
        latency: int,
        jitter: float
    ) -> orm.WebRTCConnectionORM:
        room_uuid = uuid.UUID(room_id)
        
        conn = self.db.query(orm.WebRTCConnectionORM).filter(
            orm.WebRTCConnectionORM.webrtc_room_id == room_uuid,
            orm.WebRTCConnectionORM.peer_id == peer_id
        ).first()

        if conn:
            conn.connection_state = state
            conn.packet_loss = packet_loss
            conn.latency_ms = latency
            conn.jitter_ms = jitter
            conn.updated_at = datetime.now(timezone.utc)
        else:
            conn = orm.WebRTCConnectionORM(
                id=uuid.uuid4(),
                webrtc_room_id=room_uuid,
                peer_id=peer_id,
                connection_state=state,
                packet_loss=packet_loss,
                latency_ms=latency,
                jitter_ms=jitter
            )
            self.db.add(conn)
        self.db.flush()
        return conn

    def log_webrtc_event(
        self,
        room_id: str,
        peer_id: Optional[str],
        event_type: str,
        details: Optional[str]
    ):
        evt = orm.WebRTCEventORM(
            id=uuid.uuid4(),
            webrtc_room_id=uuid.UUID(room_id),
            peer_id=peer_id,
            event_type=event_type,
            details=details
        )
        self.db.add(evt)
        self.db.flush()

    def commit(self):
        self.db.commit()
