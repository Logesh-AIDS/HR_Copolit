# services/candidate-service/app/delivery/http/parser_router.py
import logging
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity
from services.common.responses import make_success_response
from services.common.exceptions import NotFoundException, UnauthorizedException
from app.adapter.db.parser_repo import ParserRepository
from app.adapter.db.document_repo import DocumentRepository
from app.domain import parser_models
from app.domain.services.parser_service import ParserService, get_storage_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parser", tags=["Resume Intelligence Parser Engine"])

def get_parser_service(db: Session = Depends(get_db)) -> ParserService:
    parser_repo = ParserRepository(db)
    doc_repo = DocumentRepository(db)
    storage = get_storage_provider()
    return ParserService(parser_repo, doc_repo, storage)


@router.post("/parse/{document_id}", status_code=status.HTTP_202_ACCEPTED)
def parse_resume(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Kicks off the asynchronous parsing pipeline for the specified resume document.
    """
    job_id = service.enqueue_parsing_job(document_id, current_user.id, background_tasks)
    return make_success_response({
        "parsed_resume_id": job_id,
        "status": "PENDING",
        "message": "Resume parsing initiated asynchronously."
    })


@router.get("/status/{document_id}")
def get_parsing_status(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Retrieves the parsing job status (PENDING, PARSING, COMPLETED, FAILED).
    """
    db_pr = service.parser_repo.get_parsed_resume_by_document(document_id)
    if not db_pr:
        raise NotFoundException("No parsing job records found for this document.")

    # Validate ownership
    if "ADMINISTRATOR" not in current_user.roles and str(db_pr.user_id) != current_user.id:
        raise UnauthorizedException("Access denied. You do not own this document's parsed data.")

    return make_success_response({
        "document_id": document_id,
        "status": db_pr.status,
        "parsing_confidence": db_pr.parsing_confidence,
        "updated_at": db_pr.updated_at
    })


@router.get("/resume/{document_id}")
def get_parsed_resume(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Retrieves parsed resume database model records (including schools, jobs, and skills).
    """
    db_pr = service.parser_repo.get_parsed_resume_by_document(document_id)
    if not db_pr:
        raise NotFoundException("Parsed resume data not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_pr.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    return make_success_response({
        "id": str(db_pr.id),
        "document_id": str(db_pr.document_id),
        "status": db_pr.status,
        "first_name": db_pr.first_name,
        "last_name": db_pr.last_name,
        "email": db_pr.email,
        "phone": db_pr.phone,
        "location": db_pr.location,
        "github": db_pr.github,
        "linkedin": db_pr.linkedin,
        "portfolio": db_pr.portfolio,
        "parsing_confidence": db_pr.parsing_confidence,
        "skills": [{"name": s.name, "category": s.category} for s in db_pr.skills],
        "experience": [
            {
                "company": e.company,
                "job_title": e.job_title,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "description": e.description,
                "duration_months": e.duration_months
            } for e in db_pr.experience
        ],
        "education": [
            {
                "institution": ed.institution,
                "degree": ed.degree,
                "cgpa": ed.cgpa,
                "graduation_year": ed.graduation_year
            } for ed in db_pr.education
        ],
        "projects": [
            {
                "title": p.title,
                "description": p.description,
                "technologies": p.technologies
            } for p in db_pr.projects
        ]
    })


@router.get("/json/{document_id}", response_model=None)
def get_parsed_resume_json(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Returns the single-source-of-truth standardized Resume JSON.
    """
    db_pr = service.parser_repo.get_parsed_resume_by_document(document_id)
    if not db_pr or db_pr.status != "COMPLETED":
        raise NotFoundException("Completed parsed resume data not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(db_pr.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    # Map to standardized Pydantic JSON specification
    payload = parser_models.ParsedResumeJSON(
        document_id=str(db_pr.document_id),
        user_id=str(db_pr.user_id),
        first_name=db_pr.first_name,
        last_name=db_pr.last_name,
        email=db_pr.email,
        phone=db_pr.phone,
        location=db_pr.location,
        github=db_pr.github,
        linkedin=db_pr.linkedin,
        portfolio=db_pr.portfolio,
        skills=[parser_models.ExtractedSkill(name=s.name, category=s.category) for s in db_pr.skills],
        experience=[
            parser_models.ExperienceDetail(
                company=e.company,
                job_title=e.job_title,
                start_date=e.start_date,
                end_date=e.end_date,
                description=e.description,
                duration_months=e.duration_months
            ) for e in db_pr.experience
        ],
        education=[
            parser_models.EducationDetail(
                institution=ed.institution,
                degree=ed.degree,
                cgpa=ed.cgpa,
                graduation_year=ed.graduation_year
            ) for ed in db_pr.education
        ],
        projects=[
            parser_models.ProjectDetail(
                title=p.title,
                description=p.description,
                technologies=p.technologies
            ) for p in db_pr.projects
        ],
        certifications=[
            parser_models.CertificationDetail(
                name=c.name,
                issuing_organization=c.issuing_organization,
                issue_date=c.issue_date
            ) for c in db_pr.certifications
        ],
        languages=[
            parser_models.LanguageDetail(
                name=l.name,
                proficiency=l.proficiency
            ) for l in db_pr.languages
        ],
        parsing_confidence=db_pr.parsing_confidence,
        status=db_pr.status
    )
    return make_success_response(payload.model_dump())


@router.get("/logs/{document_id}")
def get_parser_logs(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Returns parsing activity audit logs.
    """
    # Simply retrieves document details
    doc = service.doc_repo.get_document_by_id(document_id)
    if not doc:
        raise NotFoundException("Document not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(doc.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    logs = service.parser_repo.get_parsing_logs(document_id)
    log_responses = [
        {
            "id": str(log.id),
            "log_level": log.log_level,
            "message": log.message,
            "created_at": log.created_at
        } for log in logs
    ]
    return make_success_response(log_responses)


@router.post("/reprocess/{document_id}", status_code=status.HTTP_202_ACCEPTED)
def reprocess_resume(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Triggers reprocessing of a resume document.
    """
    job_id = service.enqueue_parsing_job(document_id, current_user.id, background_tasks)
    
    # Log Reprocess action
    service.parser_repo.log_parsing_event(document_id, "INFO", "Reprocessing triggered by user.")
    logger.info(f"[EVENT: ResumeReprocessed] Document: {document_id}")

    return make_success_response({
        "parsed_resume_id": job_id,
        "status": "PENDING",
        "message": "Reprocessing initiated successfully."
    })


@router.delete("/{document_id}")
def delete_parsed_data(
    document_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: ParserService = Depends(get_parser_service)
):
    """
    Deletes all parsed resume relational records.
    """
    # Pre-verify ownership
    doc = service.doc_repo.get_document_by_id(document_id)
    if not doc:
        raise NotFoundException("Document not found.")

    if "ADMINISTRATOR" not in current_user.roles and str(doc.user_id) != current_user.id:
        raise UnauthorizedException("Access denied.")

    deleted = service.parser_repo.delete_parsed_data(document_id)
    if not deleted:
        raise NotFoundException("No parsed resume data found to delete.")

    return make_success_response("Parsed resume data deleted successfully.")
