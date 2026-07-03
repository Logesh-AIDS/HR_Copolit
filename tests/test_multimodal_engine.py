import pytest
import uuid
import datetime
from unittest.mock import MagicMock

# Ensure we can import from interview-engine
import sys
import os
sys.path.insert(0, os.path.abspath("services/interview-engine"))

from app.domain.services.multimodal_service import MultimodalService
from app.domain.multimodal_models import (
    ProcessAudioRequest,
    ProcessVideoRequest,
    TimelineEventLogRequest,
    MultimodalTimelineEventCreate,
    TimelineEventType,
    FeatureSource,
    MultimodalFeatureCreate
)

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    # Setup mock behavior for get_features_by_session
    repo.get_features_by_session.return_value = []
    repo.get_timeline_events.return_value = []
    return repo

@pytest.fixture
def multimodal_service(mock_repo):
    return MultimodalService(mock_repo)

def test_process_audio(multimodal_service, mock_repo):
    session_id = uuid.uuid4()
    req = ProcessAudioRequest(
        session_id=session_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        audio_chunk_b64="dummy"
    )
    
    features = multimodal_service.process_audio(req)
    
    assert len(features) >= 3
    assert any(f.feature_name == "Speaking Speed" for f in features)
    assert any(f.feature_name == "Filler Word Density" for f in features)
    
    # Verify repo was called
    mock_repo.create_features_bulk.assert_called_once()
    saved_features = mock_repo.create_features_bulk.call_args[0][0]
    assert len(saved_features) == len(features)

def test_process_video(multimodal_service, mock_repo):
    session_id = uuid.uuid4()
    req = ProcessVideoRequest(
        session_id=session_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        video_frame_b64="dummy"
    )
    
    features = multimodal_service.process_video(req)
    
    assert len(features) >= 2
    assert any(f.feature_name == "Face Detected" for f in features)
    mock_repo.create_features_bulk.assert_called_once()
    
def test_log_timeline_events(multimodal_service, mock_repo):
    session_id = uuid.uuid4()
    events = [
        MultimodalTimelineEventCreate(
            session_id=session_id,
            event_type=TimelineEventType.RESPONSE_DELAY,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            details={"delay_ms": 1500}
        )
    ]
    req = TimelineEventLogRequest(session_id=session_id, events=events)
    
    count = multimodal_service.log_timeline_events(req)
    assert count == 1
    
    mock_repo.create_timeline_events_bulk.assert_called_once_with(events)
    mock_repo.create_features_bulk.assert_called_once()

def test_get_session_analytics(multimodal_service, mock_repo):
    session_id = uuid.uuid4()
    
    # Mock the repo returns some features
    now = datetime.datetime.now(datetime.timezone.utc)
    mock_repo.get_features_by_session.return_value = [
        MagicMock(feature_source=FeatureSource.SPEECH.value, feature_name="Filler Word Density", feature_value=0.05),
        MagicMock(feature_source=FeatureSource.VOICE.value, feature_name="Speaking Speed", feature_value=140.0),
        MagicMock(feature_source=FeatureSource.VIDEO.value, feature_name="Eye Gaze Score", feature_value=0.8),
        MagicMock(feature_source=FeatureSource.INTERACTION.value, feature_name="Response Delay", feature_value=1000.0)
    ]
    mock_repo.get_timeline_events.return_value = [
        MagicMock(event_type="RESPONSE_DELAY")
    ]
    
    analytics = multimodal_service.get_session_analytics(session_id)
    
    assert analytics.session_id == session_id
    assert analytics.total_features_extracted == 4
    assert analytics.speech_features_count == 2 # 1 speech + 1 voice
    assert analytics.video_features_count == 1
    assert analytics.interaction_events_count == 1
    assert analytics.avg_response_delay_ms == 1000.0
    assert analytics.avg_speaking_speed == 140.0
    assert analytics.avg_eye_gaze_score == 0.8
