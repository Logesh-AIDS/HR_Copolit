from fastapi import APIRouter, Depends
from app.domain.models import ComparisonRequest, ComparisonResponse
from app.domain.services.comparison_service import ComparisonService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/comparisons", tags=["Comparisons"])

def get_comparison_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return ComparisonService(pg_repo, kafka)

@router.post("", response_model=ComparisonResponse)
def compare_candidates(req: ComparisonRequest, service: ComparisonService = Depends(get_comparison_service)):
    return service.generate_comparison(req)
