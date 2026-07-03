from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import IncidentReportCreate, IncidentReportResponse

class IncidentService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def create_incident(self, incident_req: IncidentReportCreate) -> IncidentReportResponse:
        record = self.pg_repo.add_incident(incident_req)
        
        self.kafka.publish_event(
            topic="observability.incident_created",
            key=record.id,
            payload={"incident_id": record.id, "severity": record.severity, "root_cause": record.root_cause}
        )
        return IncidentReportResponse.model_validate(record)
