from fastapi import APIRouter, Depends
from app.domain.models import MockSessionRequest, MockSessionResponse
from app.domain.services.mock_interview_service import MockInterviewService
from app.adapter.db.postgres_repo import get_db, PostgresRepository
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/mock-interviews", tags=["Mock Interviews"])

def get_mock_service(db=Depends(get_db)):
    pg_repo = PostgresRepository(db)
    kafka = KafkaPublisher()
    return MockInterviewService(pg_repo, kafka)

@router.post("/start", response_model=MockSessionResponse)
def start_mock_session(req: MockSessionRequest, service: MockInterviewService = Depends(get_mock_service)):
    return service.start_mock_session(req)
