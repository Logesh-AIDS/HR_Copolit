from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

class DeploymentService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def promote_model(self, model_id: str):
        record = self.pg_repo.update_model_status(model_id, "Production")
        if record:
            self.kafka.publish_event(
                topic="model.promoted",
                key=record.id,
                payload={"model_id": record.id, "name": record.name, "version": record.version, "status": "Production"}
            )
        return record
