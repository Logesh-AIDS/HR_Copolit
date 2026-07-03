from fastapi import APIRouter, Depends
from app.domain.models import CandidateUnifiedProfile, InterviewAnalytics
from app.domain.services.candidate_service import CandidateService
from app.adapter.messaging.kafka_publisher import KafkaPublisher

router = APIRouter(prefix="/candidates", tags=["Candidates"])

def get_candidate_service():
    kafka = KafkaPublisher()
    return CandidateService(kafka)

@router.get("/{candidate_id}/profile", response_model=CandidateUnifiedProfile)
def get_candidate_profile(candidate_id: str, service: CandidateService = Depends(get_candidate_service)):
    return service.get_unified_profile(candidate_id)

@router.get("/{candidate_id}/analytics", response_model=InterviewAnalytics)
def get_candidate_analytics(candidate_id: str, service: CandidateService = Depends(get_candidate_service)):
    return service.get_interview_analytics(candidate_id)
