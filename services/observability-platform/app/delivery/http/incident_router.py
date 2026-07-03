from fastapi import APIRouter, Depends
from app.domain.models import IncidentReportCreate, IncidentReportResponse
from app.domain.services.incident_service import IncidentService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/incidents", tags=["Incidents"])

def get_incident_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return IncidentService(pg_repo, kafka)

@router.post("", response_model=IncidentReportResponse)
def create_incident(req: IncidentReportCreate, service: IncidentService = Depends(get_incident_service)):
    return service.create_incident(req)
