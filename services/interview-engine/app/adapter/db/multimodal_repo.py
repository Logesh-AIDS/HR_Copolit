from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import datetime

from app.adapter.db.orm import (
    MultimodalTimelineEventORM,
    MultimodalFeatureStoreORM,
    MultimodalModelsMetadataORM
)
from app.domain.multimodal_models import (
    MultimodalTimelineEventCreate,
    MultimodalFeatureCreate
)

class MultimodalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_timeline_event(self, event: MultimodalTimelineEventCreate) -> MultimodalTimelineEventORM:
        db_event = MultimodalTimelineEventORM(
            session_id=event.session_id,
            event_type=event.event_type.value,
            timestamp=event.timestamp,
            details=event.details
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def create_timeline_events_bulk(self, events: List[MultimodalTimelineEventCreate]) -> int:
        db_events = [
            MultimodalTimelineEventORM(
                session_id=e.session_id,
                event_type=e.event_type.value,
                timestamp=e.timestamp,
                details=e.details
            )
            for e in events
        ]
        self.db.add_all(db_events)
        self.db.commit()
        return len(db_events)

    def get_timeline_events(self, session_id: UUID) -> List[MultimodalTimelineEventORM]:
        return self.db.query(MultimodalTimelineEventORM)\
            .filter(MultimodalTimelineEventORM.session_id == session_id)\
            .order_by(MultimodalTimelineEventORM.timestamp.asc())\
            .all()

    def create_feature(self, feature: MultimodalFeatureCreate) -> MultimodalFeatureStoreORM:
        db_feature = MultimodalFeatureStoreORM(
            session_id=feature.session_id,
            feature_name=feature.feature_name,
            feature_value=feature.feature_value,
            feature_source=feature.feature_source.value,
            confidence=feature.confidence,
            model_version=feature.model_version,
            timestamp=feature.timestamp
        )
        self.db.add(db_feature)
        self.db.commit()
        self.db.refresh(db_feature)
        return db_feature

    def create_features_bulk(self, features: List[MultimodalFeatureCreate]) -> int:
        db_features = [
            MultimodalFeatureStoreORM(
                session_id=f.session_id,
                feature_name=f.feature_name,
                feature_value=f.feature_value,
                feature_source=f.feature_source.value,
                confidence=f.confidence,
                model_version=f.model_version,
                timestamp=f.timestamp
            )
            for f in features
        ]
        self.db.add_all(db_features)
        self.db.commit()
        return len(db_features)

    def get_features_by_session(self, session_id: UUID) -> List[MultimodalFeatureStoreORM]:
        return self.db.query(MultimodalFeatureStoreORM)\
            .filter(MultimodalFeatureStoreORM.session_id == session_id)\
            .order_by(MultimodalFeatureStoreORM.timestamp.asc())\
            .all()

    def get_features_by_source(self, session_id: UUID, source: str) -> List[MultimodalFeatureStoreORM]:
        return self.db.query(MultimodalFeatureStoreORM)\
            .filter(MultimodalFeatureStoreORM.session_id == session_id)\
            .filter(MultimodalFeatureStoreORM.feature_source == source)\
            .order_by(MultimodalFeatureStoreORM.timestamp.asc())\
            .all()
