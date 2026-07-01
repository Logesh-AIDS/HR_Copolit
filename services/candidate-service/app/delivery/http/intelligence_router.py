# services/candidate-service/app/delivery/http/intelligence_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, UnauthorizedException
from app.adapter.db.intelligence_repo import IntelligenceRepository
from app.adapter.db.parser_repo import ParserRepository
from app.domain import intelligence_models
from app.domain.services.intelligence_service import IntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["Resume Intelligence Profile Engine"])

def get_intelligence_service(db: Session = Depends(get_db)) -> IntelligenceService:
    intel_repo = IntelligenceRepository(db)
    parser_repo = ParserRepository(db)
    return IntelligenceService(intel_repo, parser_repo)


@router.post("/generate/{document_id}", status_code=status.HTTP_201_CREATED)
def generate_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Evaluates Candidate Resume JSON and generates intelligence profiles.
    """
    db_pr = service.parser_repo.get_parsed_resume_by_document(document_id)
    if not db_pr:
        raise NotFoundException("Parsed resume not found. Parse document first.")

    # Validate ownership
    if "ADMINISTRATOR" not in current_user.roles and str(db_pr.user_id) != current_user.id:
        raise UnauthorizedException("Access denied. You do not own this document's parsed data.")

    db_intel = service.generate_candidate_intelligence(document_id, current_user.id)
    return make_success_response({
        "intelligence_id": str(db_intel.id),
        "career_level": db_intel.career_level,
        "career_focus": db_intel.career_focus,
        "resume_completeness": db_intel.resume_completeness
    })


@router.get("/{document_id}")
def get_candidate_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Retrieves candidate intelligence profiles.
    """
    db_intel = service.intel_repo.get_intelligence_by_document(document_id)
    if not db_intel:
        raise NotFoundException("Intelligence profile not generated for this document.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_intel.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    return make_success_response({
        "id": str(db_intel.id),
        "parsed_resume_id": str(db_intel.parsed_resume_id),
        "user_id": str(db_intel.user_id),
        "document_id": str(db_intel.document_id),
        "career_level": db_intel.career_level,
        "career_focus": db_intel.career_focus,
        "preferred_roles": db_intel.preferred_roles,
        "resume_completeness": db_intel.resume_completeness,
        "experience_summary": {
            "total_experience_months": db_intel.experience_summary.total_experience_months,
            "relevant_experience_months": db_intel.experience_summary.relevant_experience_months,
            "leadership_experience_months": db_intel.experience_summary.leadership_experience_months,
            "internship_experience_months": db_intel.experience_summary.internship_experience_months,
            "project_experience_months": db_intel.experience_summary.project_experience_months
        } if db_intel.experience_summary else None,
        "skill_confidence": [
            {
                "name": s.name,
                "confidence_score": s.confidence_score,
                "experience_years": s.experience_years,
                "project_count": s.project_count,
                "recency_score": s.recency_score,
                "has_certification": s.has_certification
            } for s in db_intel.skill_confidence
        ],
        "strengths_weaknesses": [
            {"type": sw.type, "value": sw.value} for sw in db_intel.strengths_weaknesses
        ]
    })


@router.get("/graph/{document_id}")
def get_candidate_skill_graph(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Returns candidate's custom intersected skill knowledge graph.
    """
    db_intel = service.intel_repo.get_intelligence_by_document(document_id)
    if not db_intel:
        raise NotFoundException("Intelligence profile not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_intel.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    graph = service.get_candidate_skill_graph(document_id)
    return make_success_response(graph)


@router.get("/taxonomy/global")
def get_global_taxonomy(
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Returns the global technology taxonomy tree.
    """
    nodes = service.intel_repo.list_taxonomy()
    node_list = [
        {
            "concept_name": node.concept_name,
            "parent_concept_name": node.parent_concept_name,
            "relation_type": node.relation_type
        } for node in nodes
    ]
    return make_success_response(node_list)


@router.get("/experience/{document_id}")
def get_experience_breakdown(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Returns experience breakdowns.
    """
    db_intel = service.intel_repo.get_intelligence_by_document(document_id)
    if not db_intel or not db_intel.experience_summary:
        raise NotFoundException("Experience summary not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_intel.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    exp = db_intel.experience_summary
    return make_success_response({
        "total_experience_months": exp.total_experience_months,
        "relevant_experience_months": exp.relevant_experience_months,
        "leadership_experience_months": exp.leadership_experience_months,
        "internship_experience_months": exp.internship_experience_months,
        "project_experience_months": exp.project_experience_months
    })


@router.get("/features/{document_id}")
def get_candidate_features(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Returns ML feature vectors for candidate classification model training.
    """
    db_intel = service.intel_repo.get_intelligence_by_document(document_id)
    if not db_intel or not db_intel.features:
        raise NotFoundException("Feature store details not generated.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_intel.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    feat = db_intel.features
    return make_success_response({
        "skills_count": feat.skills_count,
        "projects_count": feat.projects_count,
        "avg_project_complexity": feat.avg_project_complexity,
        "years_experience": feat.years_experience,
        "education_score": feat.education_score,
        "certification_score": feat.certification_score,
        "skill_diversity": feat.skill_diversity,
        "tech_breadth": feat.tech_breadth,
        "tech_depth": feat.tech_depth,
        "leadership_score": feat.leadership_score,
        "cloud_exposure": feat.cloud_exposure,
        "deployment_experience": feat.deployment_experience
    })


@router.post("/recalculate/{document_id}")
def recalculate_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
):
    """
    Overwrites/Recalculates Candidate Intelligence Profile parameters.
    """
    db_pr = service.parser_repo.get_parsed_resume_by_document(document_id)
    if not db_pr:
        raise NotFoundException("Parsed resume not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_pr.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    db_intel = service.generate_candidate_intelligence(document_id, current_user.id)
    logger.info(f"[EVENT: CandidateIntelligenceRecalculated] ID: {db_intel.id}")
    
    return make_success_response({
        "intelligence_id": str(db_intel.id),
        "status": "RECALCULATED"
    })
