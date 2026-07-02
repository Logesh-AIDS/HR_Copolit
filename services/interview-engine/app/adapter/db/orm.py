# services/interview-engine/app/adapter/db/orm.py
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from services.common.database import Base

class InterviewPlanORM(Base):
    __tablename__ = "interview_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    candidate_level = Column(String(50), nullable=True)
    role = Column(String(255), nullable=True)
    difficulty = Column(String(50), nullable=True)
    total_duration_minutes = Column(Integer, default=60, server_default="60", nullable=False)
    passing_criteria = Column(Float().with_variant(Float(), "sqlite"), default=60.0, server_default="60.0", nullable=False)
    status = Column(String(50), default="PLANNED", server_default="PLANNED", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    blueprint = relationship("InterviewBlueprintORM", back_populates="interview_plan", uselist=False, cascade="all, delete-orphan")
    execution_state = relationship("InterviewExecutionStateORM", back_populates="interview_plan", uselist=False, cascade="all, delete-orphan")
    timelines = relationship("InterviewTimelineORM", back_populates="interview_plan", cascade="all, delete-orphan")
    decision_histories = relationship("DecisionHistoryORM", back_populates="interview_plan", cascade="all, delete-orphan")
    adaptive_decisions = relationship("AdaptiveDecisionORM", back_populates="interview_plan", cascade="all, delete-orphan")


class InterviewBlueprintORM(Base):
    __tablename__ = "interview_blueprints"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_plan_id = Column(UUID(as_uuid=True), ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    rounds_count = Column(Integer, default=0, server_default="0", nullable=False)
    termination_rules = Column(Text, nullable=True)
    adaptive_rules = Column(Text, nullable=True)
    retry_rules = Column(Text, nullable=True)
    break_rules = Column(Text, nullable=True)

    # Relationships
    interview_plan = relationship("InterviewPlanORM", back_populates="blueprint")
    rounds = relationship("RoundDefinitionORM", back_populates="blueprint", cascade="all, delete-orphan")


class RoundDefinitionORM(Base):
    __tablename__ = "round_definitions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_blueprint_id = Column(UUID(as_uuid=True), ForeignKey("interview_blueprints.id", ondelete="CASCADE"), nullable=False)
    round_index = Column(Integer, default=0, server_default="0", nullable=False)
    name = Column(String(255), nullable=False)
    objective = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)
    expected_skills = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)
    max_time_minutes = Column(Integer, default=15, server_default="15", nullable=False)
    question_count = Column(Integer, default=5, server_default="5", nullable=False)
    evaluation_strategy = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)
    failure_criteria = Column(Text, nullable=True)

    # Relationships
    blueprint = relationship("InterviewBlueprintORM", back_populates="rounds")


class InterviewExecutionStateORM(Base):
    __tablename__ = "interview_execution_states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_plan_id = Column(UUID(as_uuid=True), ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    current_round_index = Column(Integer, default=0, server_default="0", nullable=False)
    current_question_index = Column(Integer, default=0, server_default="0", nullable=False)
    current_question_id = Column(UUID(as_uuid=True), nullable=True)
    remaining_time_seconds = Column(Integer, default=3600, server_default="3600", nullable=False)
    score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    skipped_questions = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)
    candidate_actions = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)
    warnings = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)
    connection_status = Column(String(50), default="DISCONNECTED", server_default="DISCONNECTED", nullable=False)
    is_paused = Column(Boolean, default=False, server_default="false", nullable=False)
    is_completed = Column(Boolean, default=False, server_default="false", nullable=False)
    is_failed = Column(Boolean, default=False, server_default="false", nullable=False)

    # Relationships
    interview_plan = relationship("InterviewPlanORM", back_populates="execution_state")


class InterviewTimelineORM(Base):
    __tablename__ = "interview_timelines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_plan_id = Column(UUID(as_uuid=True), ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_plan = relationship("InterviewPlanORM", back_populates="timelines")


class DecisionHistoryORM(Base):
    __tablename__ = "decision_histories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_plan_id = Column(UUID(as_uuid=True), ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    decision_type = Column(String(100), nullable=False)
    rationale = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_plan = relationship("InterviewPlanORM", back_populates="decision_histories")


class AdaptiveDecisionORM(Base):
    __tablename__ = "adaptive_decisions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_plan_id = Column(UUID(as_uuid=True), ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    round_index = Column(Integer, default=0, server_default="0", nullable=False)
    trigger_event = Column(Text, nullable=False)
    adjustment_details = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_plan = relationship("InterviewPlanORM", back_populates="adaptive_decisions")


class CandidateIntelligenceORM(Base):
    __tablename__ = "candidate_intelligences"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    career_level = Column(String(50))
    career_focus = Column(String(255))
    
    # Relationships
    skill_confidence = relationship("SkillConfidenceORM", back_populates="candidate_intelligence")


class SkillConfidenceORM(Base):
    __tablename__ = "skill_confidence"
    id = Column(UUID(as_uuid=True), primary_key=True)
    candidate_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_intelligences.id"))
    name = Column(String(100), nullable=False)
    confidence_score = Column(Float())

    # Relationships
    candidate_intelligence = relationship("CandidateIntelligenceORM", back_populates="skill_confidence")


class JobIntelligenceORM(Base):
    __tablename__ = "job_intelligences"
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255))
    experience_years_required = Column(Integer)
    expected_seniority = Column(String(50))

    # Relationships
    skills = relationship("JobRequiredSkillORM", back_populates="job_intelligence")


class JobRequiredSkillORM(Base):
    __tablename__ = "job_required_skills"
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligences.id"))
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    is_mandatory = Column(Boolean)

    # Relationships
    job_intelligence = relationship("JobIntelligenceORM", back_populates="skills")


class CandidateORM(Base):
    __tablename__ = "candidates"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    resume_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JobORM(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("recruiters.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    experience_level = Column(String(50), nullable=False)
    department = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InterviewSessionORM(Base):
    __tablename__ = "interview_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), nullable=False)
    interview_plan_id = Column(UUID(as_uuid=True), ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=True)
    session_token = Column(String(512), unique=True, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_plan = relationship("InterviewPlanORM")
    runtime_state = relationship("SessionRuntimeStateORM", back_populates="interview_session", uselist=False, cascade="all, delete-orphan")
    state_histories = relationship("StateHistoryORM", back_populates="interview_session", cascade="all, delete-orphan")
    round_progress = relationship("RoundProgressORM", back_populates="interview_session", cascade="all, delete-orphan")
    question_progress = relationship("QuestionProgressORM", back_populates="interview_session", cascade="all, delete-orphan")
    events = relationship("RuntimeEventORM", back_populates="interview_session", cascade="all, delete-orphan")
    timer_snapshots = relationship("TimerSnapshotORM", back_populates="interview_session", cascade="all, delete-orphan")
    connection_logs = relationship("ConnectionLogORM", back_populates="interview_session", cascade="all, delete-orphan")
    recovery_logs = relationship("RecoveryLogORM", back_populates="interview_session", cascade="all, delete-orphan")


class SessionRuntimeStateORM(Base):
    __tablename__ = "session_runtime_states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    current_round_index = Column(Integer, default=0, server_default="0", nullable=False)
    current_question_index = Column(Integer, default=0, server_default="0", nullable=False)
    current_difficulty = Column(String(50), default="MEDIUM", server_default="MEDIUM", nullable=False)
    current_score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    remaining_time_seconds = Column(Integer, default=3600, server_default="3600", nullable=False)
    connection_status = Column(String(50), default="DISCONNECTED", server_default="DISCONNECTED", nullable=False)
    warnings_count = Column(Integer, default=0, server_default="0", nullable=False)
    pause_count = Column(Integer, default=0, server_default="0", nullable=False)
    reconnect_attempts = Column(Integer, default=0, server_default="0", nullable=False)
    adaptive_decisions = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="runtime_state")


class StateHistoryORM(Base):
    __tablename__ = "state_histories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    transitioned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="state_histories")


class RoundProgressORM(Base):
    __tablename__ = "round_progress"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    round_index = Column(Integer, default=0, server_default="0", nullable=False)
    round_name = Column(String(255), nullable=False)
    status = Column(String(50), default="PENDING", server_default="PENDING", nullable=False)
    time_spent_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    score_awarded = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="round_progress")


class QuestionProgressORM(Base):
    __tablename__ = "question_progress"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    round_index = Column(Integer, default=0, server_default="0", nullable=False)
    question_index = Column(Integer, default=0, server_default="0", nullable=False)
    difficulty = Column(String(50), nullable=False)
    score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    time_spent_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    is_skipped = Column(Boolean, default=False, server_default="false", nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="question_progress")


class RuntimeEventORM(Base):
    __tablename__ = "runtime_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSONB().with_variant(JSON, "sqlite"), default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="events")


class TimerSnapshotORM(Base):
    __tablename__ = "timer_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    timer_name = Column(String(100), nullable=False)
    elapsed_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    remaining_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="timer_snapshots")


class ConnectionLogORM(Base):
    __tablename__ = "connection_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    event = Column(String(100), nullable=False)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="connection_logs")


class RecoveryLogORM(Base):
    __tablename__ = "recovery_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, default=1, server_default="1", nullable=False)
    success = Column(Boolean, default=False, server_default="false", nullable=False)
    restored_elapsed_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interview_session = relationship("InterviewSessionORM", back_populates="recovery_logs")


class WebRTCRoomORM(Base):
    __tablename__ = "webrtc_rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="ACTIVE", server_default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    connections = relationship("WebRTCConnectionORM", back_populates="webrtc_room", cascade="all, delete-orphan")
    events = relationship("WebRTCEventORM", back_populates="webrtc_room", cascade="all, delete-orphan")


class WebRTCConnectionORM(Base):
    __tablename__ = "webrtc_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webrtc_room_id = Column(UUID(as_uuid=True), ForeignKey("webrtc_rooms.id", ondelete="CASCADE"), nullable=False)
    peer_id = Column(String(100), nullable=False)
    connection_state = Column(String(50), default="NEW", server_default="NEW", nullable=False)
    packet_loss = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    latency_ms = Column(Integer, default=0, server_default="0", nullable=False)
    jitter_ms = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    webrtc_room = relationship("WebRTCRoomORM", back_populates="connections")


class WebRTCEventORM(Base):
    __tablename__ = "webrtc_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webrtc_room_id = Column(UUID(as_uuid=True), ForeignKey("webrtc_rooms.id", ondelete="CASCADE"), nullable=False)
    peer_id = Column(String(100), nullable=True)
    event_type = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    webrtc_room = relationship("WebRTCRoomORM", back_populates="events")


class CollaborationChatORM(Base):
    __tablename__ = "collaboration_chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String(100), nullable=False)
    recipient_id = Column(String(100), nullable=True)
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CollaborationWhiteboardORM(Base):
    __tablename__ = "collaboration_whiteboards"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CollaborationFileORM(Base):
    __tablename__ = "collaboration_files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    uploader_id = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CollaborationNoteORM(Base):
    __tablename__ = "collaboration_notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    author_role = Column(String(50), nullable=False)
    notes_content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=True, server_default="true", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class QuestionORM(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=False)
    problem_statement = Column(Text, nullable=False)
    question_metadata = Column("metadata", JSONB().with_variant(JSON, "sqlite"), default={}, nullable=False)


class QuestionRubricORM(Base):
    __tablename__ = "question_rubrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    criteria = Column(String(255), nullable=False)
    max_score = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QuestionVersionORM(Base):
    __tablename__ = "question_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    statement_snapshot = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QuestionRetrievalLogORM(Base):
    __tablename__ = "question_retrieval_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    retrieval_strategy = Column(String(100), nullable=False)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CodingProblemORM(Base):
    __tablename__ = "coding_problems"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    statement = Column(Text, nullable=False)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    time_limit_ms = Column(Integer, default=2000, server_default="2000", nullable=False)
    memory_limit_bytes = Column(Integer, default=268435456, server_default="268435456", nullable=False)
    reference_solution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CodingTestCaseORM(Base):
    __tablename__ = "coding_test_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False, server_default="false", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CodeSubmissionORM(Base):
    __tablename__ = "code_submissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_attempt_id = Column(UUID(as_uuid=True), ForeignKey("question_attempts.id", ondelete="CASCADE"), nullable=False)
    source_code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    test_cases_passed = Column(Integer, nullable=False)
    total_test_cases = Column(Integer, nullable=False)
    execution_time_ms = Column(Float, nullable=True)
    memory_used_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CompilationLogORM(Base):
    __tablename__ = "compilation_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("code_submissions.id", ondelete="CASCADE"), nullable=False)
    logs = Column(Text, nullable=False)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExecutionResultORM(Base):
    __tablename__ = "execution_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("code_submissions.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("coding_test_cases.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False)
    actual_output = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    memory_used_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QuestionAttemptORM(Base):
    __tablename__ = "question_attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    time_spent_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    response_transcript = Column(Text, nullable=True)
    auto_score = Column(Float, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
