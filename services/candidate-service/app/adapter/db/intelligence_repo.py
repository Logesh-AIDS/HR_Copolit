# services/candidate-service/app/adapter/db/intelligence_repo.py
import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

class IntelligenceRepository(SQLAlchemyRepository):
    """
    Handles database operations for candidate intelligence, summaries, features, and technology taxonomy.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def get_intelligence_by_document(self, document_id: str) -> Optional[orm.CandidateIntelligenceORM]:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            return None
        return self.db.query(orm.CandidateIntelligenceORM).filter(
            orm.CandidateIntelligenceORM.document_id == doc_uuid
        ).first()

    def get_intelligence_by_user(self, user_id: str) -> Optional[orm.CandidateIntelligenceORM]:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        return self.db.query(orm.CandidateIntelligenceORM).filter(
            orm.CandidateIntelligenceORM.user_id == user_uuid
        ).first()

    def create_or_clear_intelligence(self, parsed_resume_id: str, user_id: str, document_id: str) -> orm.CandidateIntelligenceORM:
        """
        Creates or overwrites the CandidateIntelligence wrapper.
        """
        # Purge existing if present to ensure clean updates
        existing = self.get_intelligence_by_document(document_id)
        if existing:
            self.db.delete(existing)
            self.db.commit()

        intel = orm.CandidateIntelligenceORM(
            parsed_resume_id=uuid.UUID(parsed_resume_id),
            user_id=uuid.UUID(user_id),
            document_id=uuid.UUID(document_id)
        )
        return self.add(intel)

    def save_intelligence_details(
        self,
        intelligence_id: str,
        career_level: str,
        career_focus: str,
        preferred_roles: List[str],
        resume_completeness: float,
        exp_summary_data: dict,
        skill_conf_data: List[dict],
        features_data: dict,
        str_weak_data: List[dict]
    ) -> orm.CandidateIntelligenceORM:
        try:
            intel_uuid = uuid.UUID(intelligence_id)
        except ValueError:
            raise ValueError("Invalid intelligence ID format.")

        db_intel = self.db.query(orm.CandidateIntelligenceORM).filter(
            orm.CandidateIntelligenceORM.id == intel_uuid
        ).first()
        if not db_intel:
            raise ValueError("Target intelligence profile not found.")

        # 1. Update core fields
        db_intel.career_level = career_level
        db_intel.career_focus = career_focus
        db_intel.preferred_roles = preferred_roles
        db_intel.resume_completeness = resume_completeness

        # 2. Clear old children (cascade orphan deletes from lists)
        db_intel.skill_confidence.clear()
        db_intel.strengths_weaknesses.clear()

        # 3. Save experience summary
        if db_intel.experience_summary:
            self.db.delete(db_intel.experience_summary)
        
        db_intel.experience_summary = orm.ExperienceSummaryORM(
            total_experience_months=exp_summary_data.get("total_experience_months", 0),
            relevant_experience_months=exp_summary_data.get("relevant_experience_months", 0),
            leadership_experience_months=exp_summary_data.get("leadership_experience_months", 0),
            internship_experience_months=exp_summary_data.get("internship_experience_months", 0),
            project_experience_months=exp_summary_data.get("project_experience_months", 0)
        )

        # 4. Save features
        if db_intel.features:
            self.db.delete(db_intel.features)
            
        db_intel.features = orm.FeatureStoreORM(
            skills_count=features_data.get("skills_count", 0),
            projects_count=features_data.get("projects_count", 0),
            avg_project_complexity=features_data.get("avg_project_complexity", 0.0),
            years_experience=features_data.get("years_experience", 0.0),
            education_score=features_data.get("education_score", 0.0),
            certification_score=features_data.get("certification_score", 0.0),
            skill_diversity=features_data.get("skill_diversity", 0.0),
            tech_breadth=features_data.get("tech_breadth", 0.0),
            tech_depth=features_data.get("tech_depth", 0.0),
            leadership_score=features_data.get("leadership_score", 0.0),
            cloud_exposure=features_data.get("cloud_exposure", False),
            deployment_experience=features_data.get("deployment_experience", False)
        )

        # 5. Save skill confidence metrics
        for sc in skill_conf_data:
            db_intel.skill_confidence.append(
                orm.SkillConfidenceORM(
                    name=sc["name"],
                    confidence_score=sc["confidence_score"],
                    experience_years=sc["experience_years"],
                    project_count=sc["project_count"],
                    recency_score=sc["recency_score"],
                    has_certification=sc["has_certification"]
                )
            )

        # 6. Save strengths & weaknesses
        for sw in str_weak_data:
            db_intel.strengths_weaknesses.append(
                orm.CandidateStrengthWeaknessORM(
                    type=sw["type"],
                    value=sw["value"]
                )
            )

        self.db.commit()
        return db_intel

    # --- Technology Taxonomy Methods ---

    def list_taxonomy(self) -> List[orm.TechnologyTaxonomyORM]:
        return self.db.query(orm.TechnologyTaxonomyORM).all()

    def seed_taxonomy_if_empty(self, taxonomy_nodes: List[dict]) -> None:
        """
        Seeds taxonomy concept connections in DB if empty.
        """
        count = self.db.query(orm.TechnologyTaxonomyORM).count()
        if count == 0:
            logger.info(f"Seeding base Technology Taxonomy graph ({len(taxonomy_nodes)} connections).")
            for node in taxonomy_nodes:
                db_node = orm.TechnologyTaxonomyORM(
                    concept_name=node["concept_name"],
                    parent_concept_name=node.get("parent_concept_name"),
                    relation_type=node.get("relation_type", "subconcept_of")
                )
                self.db.add(db_node)
            self.db.commit()
