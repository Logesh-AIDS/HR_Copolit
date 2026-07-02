# services/candidate-service/app/adapter/db/orm.py
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Boolean, Table, JSON, BigInteger, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.adapter.db.database import Base

# Junction Table: Role <-> Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

# Junction Table: User <-> Role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
)


class PermissionORM(Base):
    __tablename__ = "permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RoleORM(Base):
    __tablename__ = "roles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to Permissions
    permissions = relationship("PermissionORM", secondary=role_permissions, lazy="joined")


class UserORM(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, server_default="true", nullable=False)
    is_verified = Column(Boolean, default=False, server_default="false", nullable=False)
    failed_login_attempts = Column(Integer, default=0, server_default="0", nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    roles = relationship("RoleORM", secondary=user_roles, lazy="joined")
    candidate_profile = relationship("CandidateORM", back_populates="user", uselist=False)
    recruiter_profile = relationship("RecruiterORM", back_populates="user", uselist=False)


class RecruiterORM(Base):
    __tablename__ = "recruiters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship back to User
    user = relationship("UserORM", back_populates="recruiter_profile")


class JobORM(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    department = Column(String(100))
    experience_level = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CandidateORM(Base):
    __tablename__ = "candidates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    resume_url = Column(Text, nullable=False)
    parsed_skills = Column(JSONB().with_variant(JSON, "sqlite"), default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship back to User
    user = relationship("UserORM", back_populates="candidate_profile")


class ApplicationORM(Base):
    __tablename__ = "applications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="APPLIED", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InterviewSessionORM(Base):
    __tablename__ = "interview_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
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


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, server_default="false", nullable=False)
    replaced_by = Column(UUID(as_uuid=True), ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PasswordResetTokenORM(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, server_default="false", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmailVerificationTokenORM(Base):
    __tablename__ = "email_verification_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, server_default="false", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserSessionORM(Base):
    __tablename__ = "user_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_key = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, server_default="true", nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LoginHistoryORM(Base):
    __tablename__ = "login_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLogORM(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSONB().with_variant(JSON, "sqlite"), default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DocumentORM(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)
    current_version = Column(Integer, default=1, server_default="1", nullable=False)
    is_archived = Column(Boolean, default=False, server_default="false", nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    versions = relationship("DocumentVersionORM", back_populates="document", order_by="DocumentVersionORM.version.desc()", cascade="all, delete-orphan")


class DocumentVersionORM(Base):
    __tablename__ = "document_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger().with_variant(Integer(), "sqlite"), nullable=False)
    mime_type = Column(String(100), nullable=False)
    original_name = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    document = relationship("DocumentORM", back_populates="versions")


class DocumentActivityLogORM(Base):
    __tablename__ = "document_activity_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSONB().with_variant(JSON, "sqlite"), default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ParsedResumeORM(Base):
    __tablename__ = "parsed_resumes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    github = Column(String(255), nullable=True)
    linkedin = Column(String(255), nullable=True)
    portfolio = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    raw_text = Column(Text, nullable=True)
    parsing_confidence = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    sections = relationship("ResumeSectionORM", back_populates="parsed_resume", cascade="all, delete-orphan")
    skills = relationship("ExtractedSkillORM", back_populates="parsed_resume", cascade="all, delete-orphan")
    experience = relationship("ExperienceORM", back_populates="parsed_resume", cascade="all, delete-orphan")
    education = relationship("EducationORM", back_populates="parsed_resume", cascade="all, delete-orphan")
    projects = relationship("ProjectORM", back_populates="parsed_resume", cascade="all, delete-orphan")
    certifications = relationship("CertificationORM", back_populates="parsed_resume", cascade="all, delete-orphan")
    languages = relationship("LanguageORM", back_populates="parsed_resume", cascade="all, delete-orphan")


class ResumeSectionORM(Base):
    __tablename__ = "resume_sections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="sections")


class ExtractedSkillORM(Base):
    __tablename__ = "extracted_skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="skills")


class ExperienceORM(Base):
    __tablename__ = "experience"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    duration_months = Column(Integer, default=0, server_default="0", nullable=False)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="experience")


class EducationORM(Base):
    __tablename__ = "education"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    institution = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    cgpa = Column(String(50), nullable=True)
    graduation_year = Column(Integer, nullable=True)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="education")


class ProjectORM(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    technologies = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="projects")


class CertificationORM(Base):
    __tablename__ = "certifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=True)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="certifications")


class LanguageORM(Base):
    __tablename__ = "languages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    proficiency = Column(String(100), nullable=True)

    # Relationships
    parsed_resume = relationship("ParsedResumeORM", back_populates="languages")


class ParsingLogORM(Base):
    __tablename__ = "parsing_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    log_level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CandidateIntelligenceORM(Base):
    __tablename__ = "candidate_intelligences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_resume_id = Column(UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    career_level = Column(String(50), nullable=True)
    career_focus = Column(String(255), nullable=True)
    preferred_roles = Column(JSONB().with_variant(JSON, "sqlite"), default=[], nullable=False)
    resume_completeness = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    experience_summary = relationship("ExperienceSummaryORM", back_populates="candidate_intelligence", uselist=False, cascade="all, delete-orphan")
    skill_confidence = relationship("SkillConfidenceORM", back_populates="candidate_intelligence", cascade="all, delete-orphan")
    features = relationship("FeatureStoreORM", back_populates="candidate_intelligence", uselist=False, cascade="all, delete-orphan")
    strengths_weaknesses = relationship("CandidateStrengthWeaknessORM", back_populates="candidate_intelligence", cascade="all, delete-orphan")


class ExperienceSummaryORM(Base):
    __tablename__ = "experience_summaries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_intelligences.id", ondelete="CASCADE"), nullable=False)
    total_experience_months = Column(Integer, default=0, server_default="0", nullable=False)
    relevant_experience_months = Column(Integer, default=0, server_default="0", nullable=False)
    leadership_experience_months = Column(Integer, default=0, server_default="0", nullable=False)
    internship_experience_months = Column(Integer, default=0, server_default="0", nullable=False)
    project_experience_months = Column(Integer, default=0, server_default="0", nullable=False)

    # Relationships
    candidate_intelligence = relationship("CandidateIntelligenceORM", back_populates="experience_summary")


class SkillConfidenceORM(Base):
    __tablename__ = "skill_confidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_intelligences.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    confidence_score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    experience_years = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    project_count = Column(Integer, default=0, server_default="0", nullable=False)
    recency_score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    has_certification = Column(Boolean, default=False, server_default="false", nullable=False)

    # Relationships
    candidate_intelligence = relationship("CandidateIntelligenceORM", back_populates="skill_confidence")


class FeatureStoreORM(Base):
    __tablename__ = "feature_store"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_intelligences.id", ondelete="CASCADE"), nullable=False)
    skills_count = Column(Integer, default=0, server_default="0", nullable=False)
    projects_count = Column(Integer, default=0, server_default="0", nullable=False)
    avg_project_complexity = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    years_experience = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    education_score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    certification_score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    skill_diversity = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    tech_breadth = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    tech_depth = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    leadership_score = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    cloud_exposure = Column(Boolean, default=False, server_default="false", nullable=False)
    deployment_experience = Column(Boolean, default=False, server_default="false", nullable=False)

    # Relationships
    candidate_intelligence = relationship("CandidateIntelligenceORM", back_populates="features")


class CandidateStrengthWeaknessORM(Base):
    __tablename__ = "candidate_strengths_weaknesses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_intelligences.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)

    # Relationships
    candidate_intelligence = relationship("CandidateIntelligenceORM", back_populates="strengths_weaknesses")


class TechnologyTaxonomyORM(Base):
    __tablename__ = "technology_taxonomy"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_name = Column(String(100), nullable=False)
    parent_concept_name = Column(String(100), nullable=True)
    relation_type = Column(String(100), nullable=False)


class JobIntelligenceORM(Base):
    __tablename__ = "job_intelligences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    employment_type = Column(String(50), nullable=True)
    experience_years_required = Column(Integer, default=0, server_default="0", nullable=False)
    expected_seniority = Column(String(50), nullable=True)
    interview_difficulty = Column(String(50), nullable=True)
    education_requirements = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    skills = relationship("JobRequiredSkillORM", back_populates="job_intelligence", cascade="all, delete-orphan")
    responsibilities = relationship("JobResponsibilityORM", back_populates="job_intelligence", cascade="all, delete-orphan")
    features = relationship("JobFeatureStoreORM", back_populates="job_intelligence", uselist=False, cascade="all, delete-orphan")
    metadata_items = relationship("JobMetadataORM", back_populates="job_intelligence", cascade="all, delete-orphan")
    audit_logs = relationship("JobAuditLogORM", back_populates="job_intelligence", cascade="all, delete-orphan")


class JobRequiredSkillORM(Base):
    __tablename__ = "job_required_skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligences.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    is_mandatory = Column(Boolean, default=True, server_default="true", nullable=False)

    # Relationships
    job_intelligence = relationship("JobIntelligenceORM", back_populates="skills")


class JobResponsibilityORM(Base):
    __tablename__ = "job_responsibilities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligences.id", ondelete="CASCADE"), nullable=False)
    value = Column(Text, nullable=False)

    # Relationships
    job_intelligence = relationship("JobIntelligenceORM", back_populates="responsibilities")


class JobFeatureStoreORM(Base):
    __tablename__ = "job_feature_store"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligences.id", ondelete="CASCADE"), nullable=False)
    required_skills_count = Column(Integer, default=0, server_default="0", nullable=False)
    skill_diversity = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    required_experience = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    cloud_requirement = Column(Boolean, default=False, server_default="false", nullable=False)
    leadership_requirement = Column(Boolean, default=False, server_default="false", nullable=False)
    ai_requirement = Column(Boolean, default=False, server_default="false", nullable=False)
    programming_depth = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)
    technology_breadth = Column(Float().with_variant(Float(), "sqlite"), default=0.0, server_default="0.0", nullable=False)

    # Relationships
    job_intelligence = relationship("JobIntelligenceORM", back_populates="features")


class JobMetadataORM(Base):
    __tablename__ = "job_metadata"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligences.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)

    # Relationships
    job_intelligence = relationship("JobIntelligenceORM", back_populates="metadata_items")


class JobAuditLogORM(Base):
    __tablename__ = "job_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_intelligence_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligences.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    job_intelligence = relationship("JobIntelligenceORM", back_populates="audit_logs")


class InterviewPlanORM(Base):
    __tablename__ = "interview_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
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
