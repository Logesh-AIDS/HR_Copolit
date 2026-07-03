from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import TraceSpanCreate, TraceSpanResponse

class TracingService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def record_span(self, trace_req: TraceSpanCreate) -> TraceSpanResponse:
        record = self.pg_repo.add_trace(trace_req)
        
        # Publish event for High Latency if duration > 1000ms
        if trace_req.duration_ms > 1000:
            self.kafka.publish_event(
                topic="observability.high_latency_detected",
                key=record.trace_id,
                payload={"trace_id": record.trace_id, "service": record.service_name, "duration": record.duration_ms}
            )
            
        return TraceSpanResponse.model_validate(record)
