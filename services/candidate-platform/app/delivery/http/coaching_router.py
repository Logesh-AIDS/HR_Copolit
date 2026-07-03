from fastapi import APIRouter, Depends
from app.domain.models import LearningPlanRequest, LearningPlanResponse, AICoachFeedbackRequest, AICoachFeedbackResponse
from app.domain.services.coaching_service import CoachingService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/coach", tags=["AI Coach"])

def get_coaching_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return CoachingService(pg_repo, kafka)

@router.post("/learning-plan", response_model=LearningPlanResponse)
def generate_learning_plan(req: LearningPlanRequest, service: CoachingService = Depends(get_coaching_service)):
    return service.generate_learning_plan(req)

@router.post("/feedback", response_model=AICoachFeedbackResponse)
def get_coach_feedback(req: AICoachFeedbackRequest, service: CoachingService = Depends(get_coaching_service)):
    return service.get_coach_feedback(req)
