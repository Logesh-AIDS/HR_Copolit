from fastapi import APIRouter, Depends
from app.domain.models import MetricEventCreate, MetricEventResponse
from app.domain.services.metrics_service import MetricsService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/metrics", tags=["Metrics"])

def get_metrics_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return MetricsService(pg_repo, kafka)

@router.post("", response_model=MetricEventResponse)
def record_metric(req: MetricEventCreate, service: MetricsService = Depends(get_metrics_service)):
    return service.record_metric(req)
