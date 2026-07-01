# services/candidate-service/app/domain/intelligence_models.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class SkillConfidenceResponse(BaseModel):
    name: str
    confidence_score: float
    experience_years: float
    project_count: int
    recency_score: float
    has_certification: bool

    class Config:
        from_attributes = True


class ExperienceSummaryResponse(BaseModel):
    total_experience_months: int
    relevant_experience_months: int
    leadership_experience_months: int
    internship_experience_months: int
    project_experience_months: int

    class Config:
        from_attributes = True


class FeatureStoreResponse(BaseModel):
    skills_count: int
    projects_count: int
    avg_project_complexity: float
    years_experience: float
    education_score: float
    certification_score: float
    skill_diversity: float
    tech_breadth: float
    tech_depth: float
    leadership_score: float
    cloud_exposure: bool
    deployment_experience: bool

    class Config:
        from_attributes = True


class StrengthWeaknessResponse(BaseModel):
    type: str
    value: str

    class Config:
        from_attributes = True


class CandidateIntelligenceResponse(BaseModel):
    id: str
    parsed_resume_id: str
    user_id: str
    document_id: str
    career_level: Optional[str] = None
    career_focus: Optional[str] = None
    preferred_roles: List[str] = []
    resume_completeness: float = 0.0
    experience_summary: Optional[ExperienceSummaryResponse] = None
    skill_confidence: List[SkillConfidenceResponse] = []
    features: Optional[FeatureStoreResponse] = None
    strengths_weaknesses: List[StrengthWeaknessResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaxonomyNodeResponse(BaseModel):
    concept_name: str
    parent_concept_name: Optional[str] = None
    relation_type: str

    class Config:
        from_attributes = True
