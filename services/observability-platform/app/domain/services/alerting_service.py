from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import AlertTriggeredCreate, AlertTriggeredResponse

class AlertingService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def trigger_alert(self, alert_req: AlertTriggeredCreate) -> AlertTriggeredResponse:
        record = self.pg_repo.add_alert(alert_req)
        
        self.kafka.publish_event(
            topic="observability.alert_triggered",
            key=record.id,
            payload={"alert_id": record.id, "severity": record.severity, "message": record.message}
        )
        return AlertTriggeredResponse.model_validate(record)
