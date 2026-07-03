from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import DatasetVersionCreate, DatasetVersionResponse

class DatasetService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def register_dataset(self, dataset_req: DatasetVersionCreate) -> DatasetVersionResponse:
        record = self.pg_repo.add_dataset(dataset_req)
        
        self.kafka.publish_event(
            topic="dataset.registered",
            key=record.id,
            payload={"dataset_id": record.id, "name": record.name, "version": record.version}
        )
        
        return DatasetVersionResponse.model_validate(record)
