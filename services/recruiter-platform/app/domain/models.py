from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class CandidateUnifiedProfile(BaseModel):
    candidate_id: str
    name: str
    skills: List[str]
    match_score: float
    interview_status: str

class AIInsight(BaseModel):
    title: str
    description: str
    evidence: List[str]
    confidence_score: float

class InterviewAnalytics(BaseModel):
    candidate_id: str
    round_name: str
    coding_score: float
    communication_score: float
    insights: List[AIInsight]

class ComparisonRequest(BaseModel):
    recruiter_id: str
    candidate_ids: List[str]

class ComparisonResponse(BaseModel):
    session_id: str
    comparison_data: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)

class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class ReportRequest(BaseModel):
    recruiter_id: str
    report_type: str
    candidate_id: Optional[str] = None

class ReportResponse(BaseModel):
    report_id: str
    report_type: str
    content: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
