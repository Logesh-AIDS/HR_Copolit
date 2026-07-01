# services/candidate-service/app/delivery/http/jd_intelligence_router.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, UnauthorizedException
from app.adapter.db.jd_intelligence_repo import JobIntelligenceRepository
from app.adapter.db.document_repo import DocumentRepository
from app.domain import jd_intelligence_models
from app.domain.services.jd_intelligence_service import JobIntelligenceService, get_storage_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs/intelligence", tags=["Job Description Intelligence Profile Engine"])

def get_job_intelligence_service(db: Session = Depends(get_db)) -> JobIntelligenceService:
    jd_repo = JobIntelligenceRepository(db)
    doc_repo = DocumentRepository(db)
    storage = get_storage_provider()
    return JobIntelligenceService(jd_repo, doc_repo, storage)


@router.post("/generate/{document_id}", status_code=status.HTTP_201_CREATED)
def generate_job_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: JobIntelligenceService = Depends(get_job_intelligence_service)
):
    """
    Ingests and parses uploaded Job Descriptions to create structured Intelligence Profiles.
    """
    doc = service.doc_repo.get_document_by_id(document_id)
    if not doc:
        raise NotFoundException("Document not found. Ingest Job Description document first.")

    # Validate recruiter role limits
    if "RECRUITER" not in current_user.roles and "ADMINISTRATOR" not in current_user.roles:
         raise UnauthorizedException("Access denied. Only recruiters can generate job requirements intelligence.")

    db_intel = service.generate_job_intelligence(document_id, current_user.id)
    return make_success_response({
        "job_intelligence_id": str(db_intel.id),
        "job_id": str(db_intel.job_id),
        "title": db_intel.title,
        "experience_years_required": db_intel.experience_years_required,
        "expected_seniority": db_intel.expected_seniority
    })


@router.get("/{document_id}")
def get_job_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: JobIntelligenceService = Depends(get_job_intelligence_service)
):
    """
    Retrieves the calculated Job Description Intelligence Profile.
    """
    db_intel = service.jd_repo.get_job_intelligence_by_document(document_id)
    if not db_intel:
        raise NotFoundException("Job intelligence profile not generated for this document.")

    return make_success_response({
        "id": str(db_intel.id),
        "job_id": str(db_intel.job_id),
        "document_id": str(db_intel.document_id) if db_intel.document_id else None,
        "title": db_intel.title,
        "department": db_intel.department,
        "company": db_intel.company,
        "location": db_intel.location,
        "employment_type": db_intel.employment_type,
        "experience_years_required": db_intel.experience_years_required,
        "expected_seniority": db_intel.expected_seniority,
        "interview_difficulty": db_intel.interview_difficulty,
        "education_requirements": db_intel.education_requirements,
        "responsibilities": [r.value for r in db_intel.responsibilities],
        "created_at": db_intel.created_at,
        "updated_at": db_intel.updated_at
    })


@router.get("/skills/{document_id}")
def get_job_required_skills(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: JobIntelligenceService = Depends(get_job_intelligence_service)
):
    """
    Returns lists of mandatory and optional skills extracted from the JD.
    """
    db_intel = service.jd_repo.get_job_intelligence_by_document(document_id)
    if not db_intel:
        raise NotFoundException("Job intelligence profile not found.")

    skills = [
        {
            "name": sk.name,
            "category": sk.category,
            "is_mandatory": sk.is_mandatory
        } for sk in db_intel.skills
    ]
    return make_success_response(skills)


@router.get("/features/{document_id}")
def get_job_features(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: JobIntelligenceService = Depends(get_job_intelligence_service)
):
    """
    Returns feature stores for matching algorithm calculations.
    """
    db_intel = service.jd_repo.get_job_intelligence_by_document(document_id)
    if not db_intel or not db_intel.features:
        raise NotFoundException("Job description features not generated.")

    feat = db_intel.features
    return make_success_response({
        "required_skills_count": feat.required_skills_count,
        "skill_diversity": feat.skill_diversity,
        "required_experience": feat.required_experience,
        "cloud_requirement": feat.cloud_requirement,
        "leadership_requirement": feat.leadership_requirement,
        "ai_requirement": feat.ai_requirement,
        "programming_depth": feat.programming_depth,
        "technology_breadth": feat.technology_breadth
    })


@router.post("/recalculate/{document_id}")
def recalculate_job_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: JobIntelligenceService = Depends(get_job_intelligence_service)
):
    """
    Overwrites/Recalculates the Job Description Intelligence Profile parameters.
    """
    db_intel = service.jd_repo.get_job_intelligence_by_document(document_id)
    if not db_intel:
        raise NotFoundException("Job intelligence profile not found.")

    if "RECRUITER" not in current_user.roles and "ADMINISTRATOR" not in current_user.roles:
         raise UnauthorizedException("Access denied.")

    db_intel = service.generate_job_intelligence(document_id, current_user.id)
    
    # Log Recalculate event
    service.jd_repo.log_job_audit_event(
        job_intelligence_id=str(db_intel.id),
        action="UPDATE",
        message="Job description intelligence profile recalculated."
    )
    logger.info(f"[EVENT: JobUpdated] ID: {db_intel.id}")

    return make_success_response({
        "job_intelligence_id": str(db_intel.id),
        "status": "RECALCULATED"
    })


@router.delete("/{document_id}")
def delete_job_intelligence(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: JobIntelligenceService = Depends(get_job_intelligence_service)
):
    """
    Deletes all parsed JD intelligence relational records.
    """
    if "RECRUITER" not in current_user.roles and "ADMINISTRATOR" not in current_user.roles:
         raise UnauthorizedException("Access denied.")

    deleted = service.jd_repo.delete_job_intelligence(document_id)
    if not deleted:
        raise NotFoundException("No job intelligence data found to delete.")

    return make_success_response("Job description intelligence profile purged successfully.")
