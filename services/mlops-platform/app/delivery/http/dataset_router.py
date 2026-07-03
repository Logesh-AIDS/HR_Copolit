from fastapi import APIRouter, Depends
from app.domain.models import DatasetVersionCreate, DatasetVersionResponse
from app.domain.services.dataset_service import DatasetService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/datasets", tags=["Datasets"])

def get_dataset_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return DatasetService(pg_repo, kafka)

@router.post("", response_model=DatasetVersionResponse)
def register_dataset(req: DatasetVersionCreate, service: DatasetService = Depends(get_dataset_service)):
    return service.register_dataset(req)
