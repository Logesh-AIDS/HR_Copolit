from fastapi import APIRouter, Depends, BackgroundTasks
from app.domain.models import TrainingRequest
from app.domain.services.training_pipeline import TrainingPipeline
from app.domain.services.registry_service import RegistryService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/training", tags=["Training"])

def get_training_pipeline(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    registry = RegistryService(pg_repo, kafka)
    return TrainingPipeline(registry, kafka)

@router.post("/run")
async def trigger_training(req: TrainingRequest, background_tasks: BackgroundTasks, pipeline: TrainingPipeline = Depends(get_training_pipeline)):
    background_tasks.add_task(pipeline.run_training_job_async, req)
    return {"status": "accepted", "message": f"Training job for {req.model_name} started in background."}
