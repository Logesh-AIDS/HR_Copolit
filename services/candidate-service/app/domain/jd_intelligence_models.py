# services/candidate-service/app/domain/jd_intelligence_models.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class JobRequiredSkillResponse(BaseModel):
    name: str
    category: str
    is_mandatory: bool

    class Config:
        from_attributes = True


class JobResponsibilityResponse(BaseModel):
    value: str

    class Config:
        from_attributes = True


class JobFeatureStoreResponse(BaseModel):
    required_skills_count: int
    skill_diversity: float
    required_experience: float
    cloud_requirement: bool
    leadership_requirement: bool
    ai_requirement: bool
    programming_depth: float
    technology_breadth: float

    class Config:
        from_attributes = True


class JobMetadataResponse(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True


class JobIntelligenceResponse(BaseModel):
    id: str
    job_id: str
    document_id: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_years_required: int = 0
    expected_seniority: Optional[str] = None
    interview_difficulty: Optional[str] = None
    education_requirements: Optional[str] = None
    skills: List[JobRequiredSkillResponse] = []
    responsibilities: List[JobResponsibilityResponse] = []
    features: Optional[JobFeatureStoreResponse] = None
    metadata_items: List[JobMetadataResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
