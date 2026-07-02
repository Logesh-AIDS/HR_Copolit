# services/interview-engine/app/domain/execution_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CreateSessionPayload(BaseModel):
    application_id: str = Field(..., description="The application reference UUID")
    interview_plan_id: str = Field(..., description="The generated interview plan UUID")

class ReconnectPayload(BaseModel):
    session_token: str = Field(..., description="Active session token for identification")
    ip_address: Optional[str] = Field(None, description="IP address of the client")
    user_agent: Optional[str] = Field(None, description="User Agent string of the client")

class SessionStateResponse(BaseModel):
    id: str
    application_id: str
    interview_plan_id: Optional[str]
    session_token: str
    status: str
    current_round_index: int
    current_question_index: int
    current_difficulty: str
    current_score: float
    remaining_time_seconds: int
    connection_status: str
    warnings_count: int
    pause_count: int
    reconnect_attempts: int

class RoundProgressResponse(BaseModel):
    round_index: int
    round_name: str
    status: str
    time_spent_seconds: int
    score_awarded: float
    completed_at: Optional[datetime]

class QuestionProgressResponse(BaseModel):
    round_index: int
    question_index: int
    difficulty: str
    score: float
    time_spent_seconds: int
    is_skipped: bool
    completed_at: Optional[datetime]

class StateHistoryResponse(BaseModel):
    from_state: str
    to_state: str
    transitioned_at: datetime
