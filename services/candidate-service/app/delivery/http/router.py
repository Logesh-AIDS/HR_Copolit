# services/candidate-service/app/delivery/http/router.py
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.adapter.db.database import get_db
from app.adapter.db.postgres_repo import PostgresRepository
from app.adapter.parser.spacy_parser import ResumeParser
from app.adapter.vector.qdrant_repo import QdrantRepository
from app.domain import models

router = APIRouter(prefix="/api/v1")

# Mount Authentication and Identity Management sub-routers
from app.delivery.http.auth_router import router as auth_router
from app.delivery.http.profile_router import router as profile_router
from app.delivery.http.session_router import router as session_router
from app.delivery.http.admin_router import router as admin_router

router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(session_router)
router.include_router(admin_router)

parser = ResumeParser()
vector_db = QdrantRepository()

# Setup Vector collection
vector_db.create_collection("candidates")

# Recruiters Endpoints
@router.post("/recruiters", status_code=201)
def create_recruiter(email: str, company_name: str, password_hash: str, db: Session = Depends(get_db)):
    repo = PostgresRepository(db)
    existing = repo.get_recruiter_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    recruiter = models.Recruiter(
        email=email,
        company_name=company_name,
        password_hash=password_hash
    )
    res = repo.create_recruiter(recruiter)
    return {"id": str(res.id), "email": res.email, "company_name": res.company_name}

# Jobs Endpoints
@router.post("/jobs", status_code=201)
def create_job(
    recruiter_id: str,
    title: str,
    description: str,
    experience_level: str,
    department: str = None,
    db: Session = Depends(get_db)
):
    repo = PostgresRepository(db)
    job = models.Job(
        recruiter_id=recruiter_id,
        title=title,
        description=description,
        department=department,
        experience_level=experience_level
    )
    res = repo.create_job(job)
    return {
        "id": str(res.id),
        "title": res.title,
        "description": res.description,
        "experience_level": res.experience_level
    }

@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    repo = PostgresRepository(db)
    jobs = repo.list_jobs()
    return [{"id": str(j.id), "title": j.title, "experience_level": j.experience_level} for j in jobs]

# Application & Ingestion Endpoints
@router.post("/candidates/apply", status_code=202)
async def apply_job(
    job_id: str,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    repo = PostgresRepository(db)
    
    # Check if job exists
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_bytes = await resume.read()
    
    # Parse Resume text
    raw_text = parser.extract_text_from_pdf(file_bytes)
    parsed = parser.parse_resume(raw_text)
    
    # Check if candidate exists, otherwise create
    candidate_orm = repo.get_candidate_by_email(parsed["email"])
    if not candidate_orm:
        candidate = models.Candidate(
            first_name=parsed["first_name"],
            last_name=parsed["last_name"],
            email=parsed["email"],
            resume_url=f"s3://resumes/{resume.filename}",
            parsed_skills={"skills": parsed["skills"]}
        )
        candidate_orm = repo.create_candidate(candidate)
        
        # Save to Qdrant
        vector_db.upsert_candidate_vector(str(candidate_orm.id), parsed["skills"])

    # Calculate match percentage
    match_score = parser.calculate_match_score(parsed["skills"], job.description)

    # Save Application
    app = models.Application(
        candidate_id=str(candidate_orm.id),
        job_id=job_id,
        status="ELIGIBLE" if match_score >= 50 else "PENDING_REVIEW"
    )
    
    try:
        app_orm = repo.create_application(app)
    except Exception:
        raise HTTPException(status_code=400, detail="Application already exists for this candidate/job")

    return {
        "application_id": str(app_orm.id),
        "status": app_orm.status,
        "candidate": {
            "name": f"{candidate_orm.first_name} {candidate_orm.last_name}",
            "email": candidate_orm.email,
            "extracted_skills": parsed["skills"]
        },
        "jd_match_percentage": match_score
    }

@router.get("/candidates/applications/{application_id}")
def get_application_status(application_id: str, db: Session = Depends(get_db)):
    repo = PostgresRepository(db)
    app = repo.get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    candidate = repo.get_candidate(str(app.candidate_id))
    return {
        "application_id": str(app.id),
        "status": app.status,
        "candidate_id": str(app.candidate_id),
        "job_id": str(app.job_id),
        "candidate": {
            "name": f"{candidate.first_name} {candidate.last_name}",
            "email": candidate.email
        }
    }

# Session Endpoints
@router.post("/interviews/sessions", status_code=201)
def start_interview_session(application_id: str, db: Session = Depends(get_db)):
    repo = PostgresRepository(db)
    app = repo.get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    session_token = secrets.token_urlsafe(64)
    session_orm = repo.create_interview_session(application_id, session_token)
    
    return {
        "session_id": str(session_orm.id),
        "session_token": session_orm.session_token,
        "websocket_url": f"ws://localhost:8000/api/v1/interview/ws?token={session_orm.session_token}",
        "stages": ["MCQ", "CODING", "SYSTEM_DESIGN"],
        "total_duration_seconds": 3600
    }
