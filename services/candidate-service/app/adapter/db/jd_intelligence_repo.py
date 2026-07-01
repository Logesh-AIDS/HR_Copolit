# services/candidate-service/app/adapter/db/jd_intelligence_repo.py
import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class JobIntelligenceRepository(SQLAlchemyRepository):
    """
    Handles database operations for job intelligence, required skills, responsibilities, and features.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def get_job_intelligence_by_job(self, job_id: str) -> Optional[orm.JobIntelligenceORM]:
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            return None
        return self.db.query(orm.JobIntelligenceORM).filter(
            orm.JobIntelligenceORM.job_id == job_uuid
        ).first()

    def get_job_intelligence_by_document(self, document_id: str) -> Optional[orm.JobIntelligenceORM]:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            return None
        return self.db.query(orm.JobIntelligenceORM).filter(
            orm.JobIntelligenceORM.document_id == doc_uuid
        ).first()

    def create_or_clear_job_intelligence(self, job_id: str, document_id: Optional[str]) -> orm.JobIntelligenceORM:
        """
        Creates or overwrites the JobIntelligence wrapper.
        """
        # Purge existing if present
        existing = self.get_job_intelligence_by_job(job_id)
        if existing:
            self.db.delete(existing)
            self.db.commit()

        intel = orm.JobIntelligenceORM(
            job_id=uuid.UUID(job_id),
            document_id=uuid.UUID(document_id) if document_id else None
        )
        return self.add(intel)

    def save_job_intelligence_details(
        self,
        job_intelligence_id: str,
        title: str,
        department: str,
        company: str,
        location: str,
        employment_type: str,
        experience_years_required: int,
        expected_seniority: str,
        interview_difficulty: str,
        education_requirements: str,
        skills_data: List[dict],
        responsibilities_data: List[str],
        features_data: dict,
        metadata_data: List[dict]
    ) -> orm.JobIntelligenceORM:
        try:
            intel_uuid = uuid.UUID(job_intelligence_id)
        except ValueError:
            raise ValueError("Invalid job intelligence ID format.")

        db_intel = self.db.query(orm.JobIntelligenceORM).filter(
            orm.JobIntelligenceORM.id == intel_uuid
        ).first()
        if not db_intel:
            raise ValueError("Target job intelligence profile not found.")

        # 1. Update core fields
        db_intel.title = title
        db_intel.department = department
        db_intel.company = company
        db_intel.location = location
        db_intel.employment_type = employment_type
        db_intel.experience_years_required = experience_years_required
        db_intel.expected_seniority = expected_seniority
        db_intel.interview_difficulty = interview_difficulty
        db_intel.education_requirements = education_requirements

        # 2. Clear old children (cascade orphan deletes from lists)
        db_intel.skills.clear()
        db_intel.responsibilities.clear()
        db_intel.metadata_items.clear()

        # 3. Save skills
        for sk in skills_data:
            db_intel.skills.append(
                orm.JobRequiredSkillORM(
                    name=sk["name"],
                    category=sk["category"],
                    is_mandatory=sk["is_mandatory"]
                )
            )

        # 4. Save responsibilities
        for resp in responsibilities_data:
            db_intel.responsibilities.append(
                orm.JobResponsibilityORM(
                    value=resp
                )
            )

        # 5. Save features
        if db_intel.features:
            self.db.delete(db_intel.features)
            
        db_intel.features = orm.JobFeatureStoreORM(
            required_skills_count=features_data.get("required_skills_count", 0),
            skill_diversity=features_data.get("skill_diversity", 0.0),
            required_experience=features_data.get("required_experience", 0.0),
            cloud_requirement=features_data.get("cloud_requirement", False),
            leadership_requirement=features_data.get("leadership_requirement", False),
            ai_requirement=features_data.get("ai_requirement", False),
            programming_depth=features_data.get("programming_depth", 0.0),
            technology_breadth=features_data.get("technology_breadth", 0.0)
        )

        # 6. Save metadata
        for meta in metadata_data:
            db_intel.metadata_items.append(
                orm.JobMetadataORM(
                    key=meta["key"],
                    value=meta["value"]
                )
            )

        self.db.commit()
        return db_intel

    def delete_job_intelligence(self, document_id: str) -> bool:
        db_intel = self.get_job_intelligence_by_document(document_id)
        if db_intel:
            self.db.delete(db_intel)
            self.db.commit()
            return True
        return False

    def log_job_audit_event(self, job_intelligence_id: str, action: str, message: str) -> orm.JobAuditLogORM:
        log = orm.JobAuditLogORM(
            job_intelligence_id=uuid.UUID(job_intelligence_id),
            action=action.upper(),
            message=message
        )
        return self.add(log)
