from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from services.common.database import get_db
from sqlalchemy.orm import Session
from services.common.responses import success_response, error_response

from app.domain.multimodal_models import (
    ProcessAudioRequest,
    ProcessVideoRequest,
    TimelineEventLogRequest,
    FeatureStoreResponse,
    SessionAnalyticsResponse
)
from app.adapter.db.multimodal_repo import MultimodalRepository
from app.domain.services.multimodal_service import MultimodalService

router = APIRouter(prefix="/api/v1/multimodal", tags=["Multimodal Engine"])

def get_multimodal_service(db: Session = Depends(get_db)) -> MultimodalService:
    repo = MultimodalRepository(db)
    return MultimodalService(repo)

@router.post("/audio")
def process_audio(
    request: ProcessAudioRequest,
    service: MultimodalService = Depends(get_multimodal_service)
):
    """
    Ingest and process an audio chunk for Speech and Voice features.
    """
    try:
        features = service.process_audio(request)
        return success_response(
            message="Audio processed successfully",
            data=[f.model_dump() for f in features]
        )
    except Exception as e:
        return error_response(f"Failed to process audio: {str(e)}", status_code=500)

@router.post("/video")
def process_video(
    request: ProcessVideoRequest,
    service: MultimodalService = Depends(get_multimodal_service)
):
    """
    Ingest and process a video frame for Vision features (Head Pose, Eye Gaze).
    """
    try:
        features = service.process_video(request)
        return success_response(
            message="Video processed successfully",
            data=[f.model_dump() for f in features]
        )
    except Exception as e:
        return error_response(f"Failed to process video: {str(e)}", status_code=500)

@router.post("/timeline")
def log_timeline_events(
    request: TimelineEventLogRequest,
    service: MultimodalService = Depends(get_multimodal_service)
):
    """
    Log interaction/timeline events and generate derived interaction features.
    """
    try:
        event_count = service.log_timeline_events(request)
        return success_response(
            message=f"Successfully logged {event_count} events",
            data={"events_logged": event_count}
        )
    except Exception as e:
        return error_response(f"Failed to log timeline events: {str(e)}", status_code=500)

@router.get("/features/{session_id}", response_model=None)
def get_session_features(
    session_id: UUID,
    service: MultimodalService = Depends(get_multimodal_service)
):
    """
    Retrieve fused feature store data for a given session.
    """
    try:
        features = service.repo.get_features_by_session(session_id)
        # Assuming we just map ORM to Pydantic
        response_data = [FeatureStoreResponse.model_validate(f).model_dump() for f in features]
        return success_response(
            message="Features retrieved successfully",
            data=response_data
        )
    except Exception as e:
        return error_response(f"Failed to retrieve features: {str(e)}", status_code=500)

@router.get("/analytics/{session_id}")
def get_session_analytics(
    session_id: UUID,
    service: MultimodalService = Depends(get_multimodal_service)
):
    """
    Retrieve aggregated session analytics based on multimodal features.
    """
    try:
        analytics = service.get_session_analytics(session_id)
        return success_response(
            message="Analytics retrieved successfully",
            data=analytics.model_dump()
        )
    except Exception as e:
        return error_response(f"Failed to retrieve analytics: {str(e)}", status_code=500)
