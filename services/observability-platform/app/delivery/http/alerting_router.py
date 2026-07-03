from fastapi import APIRouter, Depends
from app.domain.models import AlertTriggeredCreate, AlertTriggeredResponse
from app.domain.services.alerting_service import AlertingService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/alerts", tags=["Alerting"])

def get_alerting_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return AlertingService(pg_repo, kafka)

@router.post("", response_model=AlertTriggeredResponse)
def trigger_alert(req: AlertTriggeredCreate, service: AlertingService = Depends(get_alerting_service)):
    return service.trigger_alert(req)
