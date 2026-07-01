import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.domain import models
from app.adapter.db import orm

class PostgresRepository(SQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    # Recruiter CRUD
    def create_recruiter(self, recruiter: models.Recruiter) -> orm.RecruiterORM:
        db_recruiter = orm.RecruiterORM(
            email=recruiter.email,
            company_name=recruiter.company_name,
            password_hash=recruiter.password_hash
        )
        self.db.add(db_recruiter)
        self.db.commit()
        self.db.refresh(db_recruiter)
        return db_recruiter

    def get_recruiter_by_email(self, email: str) -> Optional[orm.RecruiterORM]:
        return self.db.query(orm.RecruiterORM).filter(orm.RecruiterORM.email == email).first()

    # Job CRUD
    def create_job(self, job: models.Job) -> orm.JobORM:
        db_job = orm.JobORM(
            recruiter_id=uuid.UUID(job.recruiter_id),
            title=job.title,
            description=job.description,
            department=job.department,
            experience_level=job.experience_level
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def get_job(self, job_id: str) -> Optional[orm.JobORM]:
        return self.db.query(orm.JobORM).filter(orm.JobORM.id == uuid.UUID(job_id)).first()

    def list_jobs(self) -> List[orm.JobORM]:
        return self.db.query(orm.JobORM).all()

    # Candidate CRUD
    def create_candidate(self, candidate: models.Candidate) -> orm.CandidateORM:
        db_candidate = orm.CandidateORM(
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            email=candidate.email,
            resume_url=candidate.resume_url,
            parsed_skills=candidate.parsed_skills
        )
        self.db.add(db_candidate)
        self.db.commit()
        self.db.refresh(db_candidate)
        return db_candidate

    def get_candidate(self, candidate_id: str) -> Optional[orm.CandidateORM]:
        return self.db.query(orm.CandidateORM).filter(orm.CandidateORM.id == uuid.UUID(candidate_id)).first()

    def get_candidate_by_email(self, email: str) -> Optional[orm.CandidateORM]:
        return self.db.query(orm.CandidateORM).filter(orm.CandidateORM.email == email).first()

    # Application CRUD
    def create_application(self, application: models.Application) -> orm.ApplicationORM:
        db_app = orm.ApplicationORM(
            candidate_id=uuid.UUID(application.candidate_id),
            job_id=uuid.UUID(application.job_id),
            status=application.status
        )
        self.db.add(db_app)
        self.db.commit()
        self.db.refresh(db_app)
        return db_app

    def get_application(self, application_id: str) -> Optional[orm.ApplicationORM]:
        return self.db.query(orm.ApplicationORM).filter(orm.ApplicationORM.id == uuid.UUID(application_id)).first()

    # Interview Session CRUD
    def create_interview_session(self, application_id: str, session_token: str) -> orm.InterviewSessionORM:
        db_session = orm.InterviewSessionORM(
            application_id=uuid.UUID(application_id),
            session_token=session_token,
            status="PENDING"
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: str) -> Optional[orm.InterviewSessionORM]:
        return self.db.query(orm.InterviewSessionORM).filter(orm.InterviewSessionORM.id == uuid.UUID(session_id)).first()

    def get_session_by_token(self, token: str) -> Optional[orm.InterviewSessionORM]:
        return self.db.query(orm.InterviewSessionORM).filter(orm.InterviewSessionORM.session_token == token).first()

    def update_session_status(self, session_id: str, status: str) -> Optional[orm.InterviewSessionORM]:
        db_session = self.get_session(session_id)
        if db_session:
            db_session.status = status
            self.db.commit()
            self.db.refresh(db_session)
        return db_session
