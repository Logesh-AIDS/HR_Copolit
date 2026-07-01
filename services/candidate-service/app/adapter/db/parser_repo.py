# services/candidate-service/app/adapter/db/parser_repo.py
import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.adapter.db import orm
from app.domain.parser_models import ParsedResumeJSON

logger = logging.getLogger(__name__)

class ParserRepository(SQLAlchemyRepository):
    """
    Handles database mappings and mutations for ParsedResumes and sub-entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def get_parsed_resume_by_document(self, document_id: str) -> Optional[orm.ParsedResumeORM]:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            return None
        return self.db.query(orm.ParsedResumeORM).filter(
            orm.ParsedResumeORM.document_id == doc_uuid
        ).first()

    def create_parsed_resume_placeholder(self, document_id: str, user_id: str) -> orm.ParsedResumeORM:
        """
        Creates an initial ParsedResumeORM wrapper in a 'PENDING' status state.
        """
        # Delete any existing parse wrapper for this document to avoid duplicates
        existing = self.get_parsed_resume_by_document(document_id)
        if existing:
            self.db.delete(existing)
            self.db.commit()

        placeholder = orm.ParsedResumeORM(
            document_id=uuid.UUID(document_id),
            user_id=uuid.UUID(user_id),
            status="PENDING",
            parsing_confidence=0.0
        )
        return self.add(placeholder)

    def update_status(self, parsed_resume_id: str, status: str, confidence: float = 0.0) -> None:
        try:
            pr_uuid = uuid.UUID(parsed_resume_id)
        except ValueError:
            return
        db_pr = self.db.query(orm.ParsedResumeORM).filter(orm.ParsedResumeORM.id == pr_uuid).first()
        if db_pr:
            db_pr.status = status
            if confidence > 0:
                db_pr.parsing_confidence = confidence
            self.db.commit()

    def save_parsed_details(self, parsed_resume_id: str, data: ParsedResumeJSON, raw_text: str) -> None:
        """
        Deletes old relations and saves the newly extracted structured details.
        """
        try:
            pr_uuid = uuid.UUID(parsed_resume_id)
        except ValueError:
            return

        db_pr = self.db.query(orm.ParsedResumeORM).filter(orm.ParsedResumeORM.id == pr_uuid).first()
        if not db_pr:
            return

        # 1. Update core fields
        db_pr.first_name = data.first_name
        db_pr.last_name = data.last_name
        db_pr.email = data.email
        db_pr.phone = data.phone
        db_pr.location = data.location
        db_pr.github = data.github
        db_pr.linkedin = data.linkedin
        db_pr.portfolio = data.portfolio
        db_pr.raw_text = raw_text
        db_pr.parsing_confidence = data.parsing_confidence
        db_pr.status = "COMPLETED"

        # 2. Clear old children (due to relationship cascade delete-orphan, deleting from list purges from DB)
        db_pr.sections.clear()
        db_pr.skills.clear()
        db_pr.experience.clear()
        db_pr.education.clear()
        db_pr.projects.clear()
        db_pr.certifications.clear()
        db_pr.languages.clear()

        # 3. Add education
        for edu in data.education:
            db_pr.education.append(
                orm.EducationORM(
                    institution=edu.institution,
                    degree=edu.degree,
                    cgpa=edu.cgpa,
                    graduation_year=edu.graduation_year
                )
            )

        # 4. Add experience
        for exp in data.experience:
            db_pr.experience.append(
                orm.ExperienceORM(
                    company=exp.company,
                    job_title=exp.job_title,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    description=exp.description,
                    duration_months=exp.duration_months
                )
            )

        # 5. Add projects
        for proj in data.projects:
            db_pr.projects.append(
                orm.ProjectORM(
                    title=proj.title,
                    description=proj.description,
                    technologies=proj.technologies
                )
            )

        # 6. Add skills
        for sk in data.skills:
            db_pr.skills.append(
                orm.ExtractedSkillORM(
                    name=sk.name,
                    category=sk.category
                )
            )

        # 7. Add certs
        for cert in data.certifications:
            db_pr.certifications.append(
                orm.CertificationORM(
                    name=cert.name,
                    issuing_organization=cert.issuing_organization,
                    issue_date=cert.issue_date
                )
            )

        # 8. Add languages
        for lang in data.languages:
            db_pr.languages.append(
                orm.LanguageORM(
                    name=lang.name,
                    proficiency=lang.proficiency
                )
            )

        self.db.commit()

    # Log Actions
    def log_parsing_event(self, document_id: str, log_level: str, message: str) -> orm.ParsingLogORM:
        log = orm.ParsingLogORM(
            document_id=uuid.UUID(document_id),
            log_level=log_level.upper(),
            message=message
        )
        return self.add(log)

    def get_parsing_logs(self, document_id: str) -> List[orm.ParsingLogORM]:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            return []
        return self.db.query(orm.ParsingLogORM).filter(
            orm.ParsingLogORM.document_id == doc_uuid
        ).order_by(orm.ParsingLogORM.created_at.asc()).all()

    def delete_parsed_data(self, document_id: str) -> bool:
        db_pr = self.get_parsed_resume_by_document(document_id)
        if db_pr:
            self.db.delete(db_pr)
            self.db.commit()
            return True
        return False
