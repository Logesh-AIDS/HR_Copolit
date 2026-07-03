import uuid
from typing import List
from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import ComparisonRequest, ComparisonResponse

class ComparisonService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def generate_comparison(self, req: ComparisonRequest) -> ComparisonResponse:
        record = self.pg_repo.save_comparison_session(req.recruiter_id, req.candidate_ids)
        
        # Mocked comparison logic (would fetch profiles & scores for all IDs)
        comparison_data = {
            c_id: {"skills_match": 0.85 + (i * 0.02), "coding_score": 0.90 - (i * 0.05)}
            for i, c_id in enumerate(req.candidate_ids)
        }
        
        self.kafka.publish_event(
            topic="recruiter.comparison_generated",
            key=record.id,
            payload={"session_id": record.id, "recruiter_id": req.recruiter_id}
        )
        
        return ComparisonResponse(session_id=record.id, comparison_data=comparison_data)
