from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class FeatureSource(str, Enum):
    SPEECH = "SPEECH"
    VOICE = "VOICE"
    VIDEO = "VIDEO"
    INTERACTION = "INTERACTION"

class TimelineEventType(str, Enum):
    QUESTION_START = "QUESTION_START"
    QUESTION_END = "QUESTION_END"
    RESPONSE_DELAY = "RESPONSE_DELAY"
    INTERRUPTION = "INTERRUPTION"
    MUTE_EVENT = "MUTE_EVENT"
    CAMERA_EVENT = "CAMERA_EVENT"
    SCREEN_SHARE = "SCREEN_SHARE"
    CONNECTION_ISSUE = "CONNECTION_ISSUE"

class MultimodalTimelineEventCreate(BaseModel):
    session_id: UUID
    event_type: TimelineEventType
    timestamp: datetime
    details: Optional[Dict[str, Any]] = {}

class MultimodalFeatureCreate(BaseModel):
    session_id: UUID
    feature_name: str
    feature_value: float
    feature_source: FeatureSource
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    timestamp: datetime

class ProcessAudioRequest(BaseModel):
    session_id: UUID
    timestamp: datetime
    audio_chunk_b64: str
    sample_rate: int = 16000

class ProcessVideoRequest(BaseModel):
    session_id: UUID
    timestamp: datetime
    video_frame_b64: str

class TimelineEventLogRequest(BaseModel):
    session_id: UUID
    events: List[MultimodalTimelineEventCreate]

class FeatureStoreResponse(BaseModel):
    id: UUID
    session_id: UUID
    feature_name: str
    feature_value: float
    feature_source: FeatureSource
    confidence: Optional[float]
    model_version: Optional[str]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionAnalyticsResponse(BaseModel):
    session_id: UUID
    total_features_extracted: int
    speech_features_count: int
    video_features_count: int
    interaction_events_count: int
    avg_response_delay_ms: Optional[float] = None
    avg_speaking_speed: Optional[float] = None
    avg_eye_gaze_score: Optional[float] = None
