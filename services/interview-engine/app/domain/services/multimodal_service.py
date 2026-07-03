import random
import uuid
import datetime
import base64
from typing import List, Dict, Any, Optional

from app.adapter.db.multimodal_repo import MultimodalRepository
from app.domain.multimodal_models import (
    ProcessAudioRequest,
    ProcessVideoRequest,
    TimelineEventLogRequest,
    MultimodalFeatureCreate,
    FeatureSource,
    SessionAnalyticsResponse
)

class MultimodalService:
    def __init__(self, repo: MultimodalRepository):
        self.repo = repo
        
        # We can pretend these are our active ML models
        self.speech_model_version = "whisper-v3-small"
        self.voice_model_version = "hubert-voice-v1"
        self.vision_model_version = "mediapipe-face-v2"
        self.interaction_model_version = "rules-engine-v1"

    def process_audio(self, request: ProcessAudioRequest) -> List[MultimodalFeatureCreate]:
        """
        Simulates processing an audio chunk for Speech and Voice features.
        In a real scenario, this would send `request.audio_chunk_b64` to an ASR and Voice Analysis model.
        """
        features = []
        
        # 1. Voice Features
        speaking_speed = random.uniform(120.0, 160.0) # words per minute
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Speaking Speed",
                feature_value=speaking_speed,
                feature_source=FeatureSource.VOICE,
                confidence=0.95,
                model_version=self.voice_model_version,
                timestamp=request.timestamp
            )
        )
        
        pause_duration = random.uniform(0.1, 2.5) # seconds
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Average Pause",
                feature_value=pause_duration,
                feature_source=FeatureSource.VOICE,
                confidence=0.92,
                model_version=self.voice_model_version,
                timestamp=request.timestamp
            )
        )
        
        pitch_variance = random.uniform(50.0, 150.0)
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Pitch Variance",
                feature_value=pitch_variance,
                feature_source=FeatureSource.VOICE,
                confidence=0.88,
                model_version=self.voice_model_version,
                timestamp=request.timestamp
            )
        )

        # 2. Speech Features
        filler_words_density = random.uniform(0.01, 0.10) # 1% to 10%
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Filler Word Density",
                feature_value=filler_words_density,
                feature_source=FeatureSource.SPEECH,
                confidence=0.99,
                model_version=self.speech_model_version,
                timestamp=request.timestamp
            )
        )

        # Persist features
        self.repo.create_features_bulk(features)
        return features

    def process_video(self, request: ProcessVideoRequest) -> List[MultimodalFeatureCreate]:
        """
        Simulates processing a video frame for Vision features (Head Pose, Eye Gaze, Engagement).
        """
        features = []

        # Face Detected (1.0 = true, 0.0 = false)
        face_detected = 1.0 if random.random() > 0.05 else 0.0
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Face Detected",
                feature_value=face_detected,
                feature_source=FeatureSource.VIDEO,
                confidence=0.99,
                model_version=self.vision_model_version,
                timestamp=request.timestamp
            )
        )

        # Eye Gaze Score (0.0 to 1.0)
        gaze_score = random.uniform(0.6, 1.0) if face_detected else 0.0
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Eye Gaze Score",
                feature_value=gaze_score,
                feature_source=FeatureSource.VIDEO,
                confidence=0.85,
                model_version=self.vision_model_version,
                timestamp=request.timestamp
            )
        )

        # Head Pose (Yaw)
        head_yaw = random.uniform(-15.0, 15.0) if face_detected else 0.0
        features.append(
            MultimodalFeatureCreate(
                session_id=request.session_id,
                feature_name="Head Yaw",
                feature_value=head_yaw,
                feature_source=FeatureSource.VIDEO,
                confidence=0.90,
                model_version=self.vision_model_version,
                timestamp=request.timestamp
            )
        )

        self.repo.create_features_bulk(features)
        return features

    def log_timeline_events(self, request: TimelineEventLogRequest) -> int:
        """
        Logs raw interaction/timeline events and generates derived interaction features.
        """
        # 1. Store raw timeline events
        self.repo.create_timeline_events_bulk(request.events)
        
        # 2. Derive Features (Interaction Analytics)
        features = []
        for event in request.events:
            if event.event_type == "RESPONSE_DELAY":
                delay_ms = float(event.details.get("delay_ms", 1000.0))
                features.append(
                    MultimodalFeatureCreate(
                        session_id=request.session_id,
                        feature_name="Response Delay",
                        feature_value=delay_ms,
                        feature_source=FeatureSource.INTERACTION,
                        confidence=1.0,
                        model_version=self.interaction_model_version,
                        timestamp=event.timestamp
                    )
                )
            elif event.event_type == "INTERRUPTION":
                features.append(
                    MultimodalFeatureCreate(
                        session_id=request.session_id,
                        feature_name="Interruption Event",
                        feature_value=1.0,
                        feature_source=FeatureSource.INTERACTION,
                        confidence=1.0,
                        model_version=self.interaction_model_version,
                        timestamp=event.timestamp
                    )
                )
        
        if features:
            self.repo.create_features_bulk(features)
            
        return len(request.events)

    def get_session_analytics(self, session_id: uuid.UUID) -> SessionAnalyticsResponse:
        """
        Aggregates all multimodal features into a session summary report.
        """
        all_features = self.repo.get_features_by_session(session_id)
        all_events = self.repo.get_timeline_events(session_id)
        
        speech_feats = [f for f in all_features if f.feature_source == FeatureSource.SPEECH.value]
        video_feats = [f for f in all_features if f.feature_source == FeatureSource.VIDEO.value]
        voice_feats = [f for f in all_features if f.feature_source == FeatureSource.VOICE.value]
        interaction_feats = [f for f in all_features if f.feature_source == FeatureSource.INTERACTION.value]

        # Calculate Averages
        avg_gaze = sum(f.feature_value for f in video_feats if f.feature_name == "Eye Gaze Score") / max(1, len([f for f in video_feats if f.feature_name == "Eye Gaze Score"]))
        avg_speed = sum(f.feature_value for f in voice_feats if f.feature_name == "Speaking Speed") / max(1, len([f for f in voice_feats if f.feature_name == "Speaking Speed"]))
        avg_delay = sum(f.feature_value for f in interaction_feats if f.feature_name == "Response Delay") / max(1, len([f for f in interaction_feats if f.feature_name == "Response Delay"]))

        return SessionAnalyticsResponse(
            session_id=session_id,
            total_features_extracted=len(all_features),
            speech_features_count=len(speech_feats) + len(voice_feats),
            video_features_count=len(video_feats),
            interaction_events_count=len(all_events),
            avg_response_delay_ms=avg_delay if any(f.feature_name == "Response Delay" for f in interaction_feats) else None,
            avg_speaking_speed=avg_speed if any(f.feature_name == "Speaking Speed" for f in voice_feats) else None,
            avg_eye_gaze_score=avg_gaze if any(f.feature_name == "Eye Gaze Score" for f in video_feats) else None
        )
