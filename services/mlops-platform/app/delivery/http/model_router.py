from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.domain.models import ModelVersionCreate, ModelVersionResponse
from app.domain.services.registry_service import RegistryService
from app.domain.services.deployment_service import DeploymentService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/models", tags=["Models"])

def get_registry_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return RegistryService(pg_repo, kafka)

def get_deployment_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return DeploymentService(pg_repo, kafka)

@router.post("", response_model=ModelVersionResponse)
def register_model(req: ModelVersionCreate, service: RegistryService = Depends(get_registry_service)):
    return service.register_model(req)

@router.post("/{model_id}/promote")
def promote_model(model_id: str, service: DeploymentService = Depends(get_deployment_service)):
    record = service.promote_model(model_id)
    if not record:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"status": "success", "model_id": record.id, "new_status": record.status}
