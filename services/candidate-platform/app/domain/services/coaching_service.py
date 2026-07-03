from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import LearningPlanRequest, LearningPlanResponse, AICoachFeedbackRequest, AICoachFeedbackResponse

class CoachingService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def generate_learning_plan(self, req: LearningPlanRequest) -> LearningPlanResponse:
        # Mocking the AI plan generation
        plan_content = {
            "week_1": f"Focus on {req.focus_areas[0]} basics.",
            "week_2": f"Advanced {req.focus_areas[0]} and projects.",
            "target": req.target_role
        }
        
        record = self.pg_repo.save_learning_plan(req.candidate_id, plan_content)
        
        self.kafka.publish_event(
            topic="candidate.learning_plan_generated",
            key=record.id,
            payload={"plan_id": record.id, "candidate_id": req.candidate_id}
        )
        
        return LearningPlanResponse(
            plan_id=record.id,
            candidate_id=record.candidate_id,
            plan_content=record.plan_content,
            created_at=record.created_at
        )

    def get_coach_feedback(self, req: AICoachFeedbackRequest) -> AICoachFeedbackResponse:
        # Mocking AI feedback based on a session ID
        return AICoachFeedbackResponse(
            summary=f"Feedback for session {req.interview_session_id}: Good effort overall.",
            strengths=["Clear articulation", "Clean code"],
            improvement_areas=["Optimization for space complexity"],
            practice_recommendations=["Dynamic Programming"]
        )
