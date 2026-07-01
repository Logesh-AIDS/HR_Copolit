# services/candidate-service/app/domain/parser_models.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ParsingStatus(str, Enum):
    PENDING = "PENDING"
    PARSING = "PARSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EducationDetail(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    cgpa: Optional[str] = None
    graduation_year: Optional[int] = None


class ExperienceDetail(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    duration_months: int = 0


class ProjectDetail(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = []


class CertificationDetail(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None


class LanguageDetail(BaseModel):
    name: str
    proficiency: Optional[str] = None


class ExtractedSkill(BaseModel):
    name: str
    category: str


class ParserLogResponse(BaseModel):
    id: str
    log_level: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ParsedResumeJSON(BaseModel):
    document_id: str
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    skills: List[ExtractedSkill] = []
    experience: List[ExperienceDetail] = []
    education: List[EducationDetail] = []
    projects: List[ProjectDetail] = []
    certifications: List[CertificationDetail] = []
    languages: List[LanguageDetail] = []
    parsing_confidence: float = 0.0
    status: str
