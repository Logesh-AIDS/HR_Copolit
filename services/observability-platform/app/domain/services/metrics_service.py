from datetime import datetime
from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import MetricEventCreate, MetricEventResponse

class MetricsService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def record_metric(self, metric_req: MetricEventCreate) -> MetricEventResponse:
        if not metric_req.timestamp:
            metric_req.timestamp = datetime.utcnow()
            
        record = self.pg_repo.add_metric(metric_req)
        
        # Simple rule: if drift metric > 0.5, emit drift detected
        if metric_req.metric_name == "model_drift" and metric_req.value > 0.5:
            self.kafka.publish_event(
                topic="observability.drift_detected",
                key=record.id,
                payload={"metric_id": record.id, "value": record.value, "labels": record.labels}
            )
            
        return MetricEventResponse.model_validate(record)
