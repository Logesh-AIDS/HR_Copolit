from fastapi import APIRouter, Depends
from app.domain.models import TraceSpanCreate, TraceSpanResponse
from app.domain.services.tracing_service import TracingService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/traces", tags=["Tracing"])

def get_tracing_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return TracingService(pg_repo, kafka)

@router.post("", response_model=TraceSpanResponse)
def record_span(req: TraceSpanCreate, service: TracingService = Depends(get_tracing_service)):
    return service.record_span(req)
