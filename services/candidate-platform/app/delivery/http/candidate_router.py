from fastapi import APIRouter, Depends
from app.domain.models import CandidateDashboardResponse, SkillProfileResponse
from app.domain.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidates", tags=["Candidates"])

def get_candidate_service():
    return CandidateService()

@router.get("/{candidate_id}/dashboard", response_model=CandidateDashboardResponse)
def get_dashboard(candidate_id: str, service: CandidateService = Depends(get_candidate_service)):
    return service.get_dashboard(candidate_id)

@router.get("/{candidate_id}/skills", response_model=SkillProfileResponse)
def get_skill_profile(candidate_id: str, service: CandidateService = Depends(get_candidate_service)):
    return service.get_skill_profile(candidate_id)
