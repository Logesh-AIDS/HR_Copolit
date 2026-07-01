# services/candidate-service/app/domain/models.py
import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# Domain Entities (Pure Pydantic models for business validation)
class Recruiter(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    company_name: str
    password_hash: str
    created_at: Optional[datetime] = None

class Job(BaseModel):
    id: Optional[str] = None
    recruiter_id: str
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    department: Optional[str] = None
    experience_level: str
    created_at: Optional[datetime] = None

class Candidate(BaseModel):
    id: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    resume_url: str
    parsed_skills: dict = {}
    created_at: Optional[datetime] = None

class Application(BaseModel):
    id: Optional[str] = None
    candidate_id: str
    job_id: str
    status: str = "APPLIED"
    created_at: Optional[datetime] = None

# Custom domain rules/validators
def validate_skills(skills: List[str]) -> List[str]:
    # Normalize skill names
    return [skill.strip().lower() for skill in skills if len(skill.strip()) > 0]
