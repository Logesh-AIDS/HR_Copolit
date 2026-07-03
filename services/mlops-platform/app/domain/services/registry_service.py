from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import ExperimentRunCreate, ExperimentRunResponse, ModelVersionCreate, ModelVersionResponse

class RegistryService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def log_experiment(self, exp_req: ExperimentRunCreate) -> ExperimentRunResponse:
        record = self.pg_repo.add_experiment(exp_req)
        
        self.kafka.publish_event(
            topic="experiment.logged",
            key=record.id,
            payload={"experiment_id": record.id, "model_name": record.model_name, "status": record.status}
        )
        return ExperimentRunResponse.model_validate(record)

    def register_model(self, model_req: ModelVersionCreate) -> ModelVersionResponse:
        record = self.pg_repo.add_model(model_req)
        
        self.kafka.publish_event(
            topic="model.registered",
            key=record.id,
            payload={"model_id": record.id, "name": record.name, "version": record.version}
        )
        return ModelVersionResponse.model_validate(record)
