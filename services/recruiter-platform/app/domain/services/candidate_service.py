from typing import List
from app.domain.models import CandidateUnifiedProfile, InterviewAnalytics, AIInsight
from app.adapter.messaging.kafka_publisher import KafkaPublisher

class CandidateService:
    def __init__(self, kafka: KafkaPublisher):
        self.kafka = kafka

    def get_unified_profile(self, candidate_id: str) -> CandidateUnifiedProfile:
        # In a real scenario, this would aggregate data via httpx from candidate-service, interview-engine, etc.
        profile = CandidateUnifiedProfile(
            candidate_id=candidate_id,
            name="Jane Doe",
            skills=["Python", "FastAPI", "React", "Kafka"],
            match_score=0.92,
            interview_status="Completed"
        )
        
        self.kafka.publish_event(
            topic="recruiter.candidate_viewed",
            key=candidate_id,
            payload={"candidate_id": candidate_id}
        )
        return profile

    def get_interview_analytics(self, candidate_id: str) -> InterviewAnalytics:
        # Mocking aggregated analytics
        return InterviewAnalytics(
            candidate_id=candidate_id,
            round_name="Technical Systems Design",
            coding_score=0.88,
            communication_score=0.95,
            insights=[
                AIInsight(
                    title="Strong System Architecture Skills",
                    description="Candidate consistently designed scalable microservices.",
                    evidence=["Used Kafka for decoupling", "Mentioned Redis caching"],
                    confidence_score=0.96
                )
            ]
        )
