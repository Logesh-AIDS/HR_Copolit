from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from app.domain.models import FeatureCreate, FeatureResponse
from app.domain.services.feature_service import FeatureService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.redis.redis_repo import RedisRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/features", tags=["Features"])

def get_feature_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    redis_repo = RedisRepository()
    kafka = KafkaPublisher()
    return FeatureService(pg_repo, redis_repo, kafka)

@router.post("", response_model=FeatureResponse)
def create_feature(feature: FeatureCreate, service: FeatureService = Depends(get_feature_service)):
    return service.create_feature(feature)

@router.get("/online/{entity_type}/{entity_id}/{feature_name}")
def get_online_feature(entity_type: str, entity_id: str, feature_name: str, service: FeatureService = Depends(get_feature_service)):
    val = service.get_online_feature(entity_type, entity_id, feature_name)
    if val is None:
        raise HTTPException(status_code=404, detail="Feature not found in online store")
    return {"value": val}

@router.get("/offline/{entity_type}/{entity_id}", response_model=List[FeatureResponse])
def get_offline_features(entity_type: str, entity_id: str, service: FeatureService = Depends(get_feature_service)):
    return service.get_offline_features(entity_type, entity_id)
