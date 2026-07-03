import asyncio
from typing import Dict, Any
from app.domain.models import TrainingRequest, ExperimentRunCreate, ModelVersionCreate
from app.domain.services.registry_service import RegistryService
from app.adapter.messaging.kafka_publisher import KafkaPublisher

class TrainingPipeline:
    def __init__(self, registry_service: RegistryService, kafka: KafkaPublisher):
        self.registry = registry_service
        self.kafka = kafka

    async def run_training_job_async(self, request: TrainingRequest):
        """Simulate a long-running training job in the background."""
        self.kafka.publish_event(
            topic="training.started",
            key=request.model_name,
            payload={"model": request.model_name, "dataset_id": request.dataset_version_id}
        )
        
        # 1. Load Dataset & Features
        await asyncio.sleep(1) 
        
        # 2. Train Model
        await asyncio.sleep(2)
        
        # 3. Evaluate Model
        mock_metrics = {"accuracy": 0.95, "f1_score": 0.94, "latency_ms": 45.2}
        
        # 4. Log Experiment
        exp = ExperimentRunCreate(
            model_name=request.model_name,
            hyperparameters=request.hyperparameters or {},
            metrics=mock_metrics,
            status="completed"
        )
        exp_record = self.registry.log_experiment(exp)
        
        # 5. Package & Register Model (auto-register if accuracy > 0.9)
        if mock_metrics["accuracy"] > 0.90:
            model_req = ModelVersionCreate(
                name=request.model_name,
                version=f"v1.{exp_record.id[:6]}",
                status="Staged",
                artifact_uri=f"s3://mlops-models/{request.model_name}/v1.{exp_record.id[:6]}.pkl"
            )
            self.registry.register_model(model_req)
        
        self.kafka.publish_event(
            topic="training.completed",
            key=request.model_name,
            payload={"model": request.model_name, "experiment_id": exp_record.id}
        )
