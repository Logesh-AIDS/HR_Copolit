from fastapi import APIRouter, Depends
from app.domain.models import ReportRequest, ReportResponse
from app.domain.services.reporting_service import ReportingService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/reports", tags=["Reports"])

def get_reporting_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return ReportingService(pg_repo, kafka)

@router.post("", response_model=ReportResponse)
def generate_report(req: ReportRequest, service: ReportingService = Depends(get_reporting_service)):
    return service.generate_report(req)
