# services/interview-engine/app/domain/interview_models.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class GeneratePlanPayload(BaseModel):
    candidate_id: str
    job_id: str
    company_config: Optional[dict] = Field(default_factory=dict)
    recruiter_preferences: Optional[dict] = Field(default_factory=dict)


class RoundDefinitionResponse(BaseModel):
    id: str
    round_index: int
    name: str
    objective: Optional[str] = None
    category: str
    difficulty: str
    expected_skills: List[str] = []
    max_time_minutes: int
    question_count: int
    evaluation_strategy: Optional[str] = None
    success_criteria: Optional[str] = None
    failure_criteria: Optional[str] = None

    class Config:
        from_attributes = True


class InterviewBlueprintResponse(BaseModel):
    id: str
    name: str
    rounds_count: int
    termination_rules: Optional[str] = None
    adaptive_rules: Optional[str] = None
    retry_rules: Optional[str] = None
    break_rules: Optional[str] = None
    rounds: List[RoundDefinitionResponse] = []

    class Config:
        from_attributes = True


class InterviewExecutionStateResponse(BaseModel):
    current_round_index: int
    current_question_index: int
    remaining_time_seconds: int
    score: float
    skipped_questions: List[str] = []
    candidate_actions: List[str] = []
    warnings: List[str] = []
    connection_status: str
    is_paused: bool
    is_completed: bool
    is_failed: bool

    class Config:
        from_attributes = True


class InterviewTimelineResponse(BaseModel):
    id: str
    event_type: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class InterviewPlanResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    candidate_level: Optional[str] = None
    role: Optional[str] = None
    difficulty: Optional[str] = None
    total_duration_minutes: int
    passing_criteria: float
    status: str
    blueprint: Optional[InterviewBlueprintResponse] = None
    execution_state: Optional[InterviewExecutionStateResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
