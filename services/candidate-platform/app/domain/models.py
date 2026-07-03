from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class CandidateDashboardResponse(BaseModel):
    upcoming_interviews: int
    readiness_score: float
    recent_feedback: str
    recommended_topics: List[str]

class SkillProfileResponse(BaseModel):
    technical_skills: Dict[str, float]
    behavioral_skills: Dict[str, float]

class LearningPlanRequest(BaseModel):
    candidate_id: str
    target_role: str
    focus_areas: List[str]

class LearningPlanResponse(BaseModel):
    plan_id: str
    candidate_id: str
    plan_content: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AICoachFeedbackRequest(BaseModel):
    candidate_id: str
    interview_session_id: str

class AICoachFeedbackResponse(BaseModel):
    summary: str
    strengths: List[str]
    improvement_areas: List[str]
    practice_recommendations: List[str]

class MockSessionRequest(BaseModel):
    candidate_id: str
    topic: str
    difficulty: str

class MockSessionResponse(BaseModel):
    session_id: str
    questions: List[str]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
