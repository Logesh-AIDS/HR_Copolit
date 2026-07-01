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
    session_token = Column(String(512), unique=True, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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
