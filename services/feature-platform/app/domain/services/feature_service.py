from typing import List, Optional, Any
from app.domain.models import FeatureCreate, FeatureResponse
from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.redis.redis_repo import RedisRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
import logging

logger = logging.getLogger(__name__)

class FeatureService:
    def __init__(self, pg_repo: PostgresRepository, redis_repo: RedisRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.redis_repo = redis_repo
        self.kafka = kafka

    def create_feature(self, feature: FeatureCreate) -> FeatureResponse:
        # 1. Save to Offline Store (Postgres)
        pg_record = self.pg_repo.save_feature(feature)
        
        # 2. Save to Online Store (Redis) for fast inference
        self.redis_repo.set_feature(
            entity_type=feature.entity_type,
            entity_id=feature.entity_id,
            feature_name=feature.name,
            value=feature.value
        )
        
        # 3. Publish Event
        event_payload = {
            "feature_id": pg_record.id,
            "entity_type": feature.entity_type,
            "entity_id": feature.entity_id,
            "name": feature.name
        }
        self.kafka.publish_event("feature.created", pg_record.id, event_payload)
        
        return FeatureResponse.model_validate(pg_record)

    def get_online_feature(self, entity_type: str, entity_id: str, feature_name: str) -> Optional[Any]:
        # Fast read from Redis
        return self.redis_repo.get_feature(entity_type, entity_id, feature_name)
        
    def get_offline_features(self, entity_type: str, entity_id: str) -> List[FeatureResponse]:
        # Slow batch read from Postgres
        records = self.pg_repo.get_features_by_entity(entity_type, entity_id)
        return [FeatureResponse.model_validate(r) for r in records]
