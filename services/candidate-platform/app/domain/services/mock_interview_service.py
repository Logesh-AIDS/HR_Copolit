from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher
from app.domain.models import MockSessionRequest, MockSessionResponse

class MockInterviewService:
    def __init__(self, pg_repo: PostgresRepository, kafka: KafkaPublisher):
        self.pg_repo = pg_repo
        self.kafka = kafka

    def start_mock_session(self, req: MockSessionRequest) -> MockSessionResponse:
        session_data = {
            "topic": req.topic,
            "difficulty": req.difficulty,
            "questions_assigned": [f"Explain {req.topic}", f"Implement a simple {req.topic} logic"]
        }
        
        record = self.pg_repo.save_mock_session(req.candidate_id, session_data)
        
        self.kafka.publish_event(
            topic="candidate.mock_interview_started",
            key=record.id,
            payload={"session_id": record.id, "candidate_id": req.candidate_id}
        )
        
        return MockSessionResponse(
            session_id=record.id,
            questions=session_data["questions_assigned"],
            status="started",
            created_at=record.created_at
        )
