from fastapi import APIRouter, Depends
from app.domain.models import ExperimentRunCreate, ExperimentRunResponse
from app.domain.services.registry_service import RegistryService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/experiments", tags=["Experiments"])

def get_registry_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return RegistryService(pg_repo, kafka)

@router.post("/runs", response_model=ExperimentRunResponse)
def log_experiment(req: ExperimentRunCreate, service: RegistryService = Depends(get_registry_service)):
    return service.log_experiment(req)
