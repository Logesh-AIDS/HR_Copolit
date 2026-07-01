# services/candidate-service/app/adapter/db/auth_repo.py
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from services.common.database import SQLAlchemyRepository
from app.adapter.db import orm

logger = logging.getLogger(__name__)

T = TypeVar("T")

class AuthRepository(SQLAlchemyRepository):
    """
    Extends generic SQLAlchemyRepository with custom IAM database query logic.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    # 1. User Queries
    def get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[orm.UserORM]:
        query = self.db.query(orm.UserORM).filter(orm.UserORM.email == email)
        if not include_deleted:
            query = query.filter(orm.UserORM.deleted_at == None)
        return query.first()

    def get_user_by_id(self, user_id: str, include_deleted: bool = False) -> Optional[orm.UserORM]:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        query = self.db.query(orm.UserORM).filter(orm.UserORM.id == uid)
        if not include_deleted:
            query = query.filter(orm.UserORM.deleted_at == None)
        return query.first()

    def list_users(self, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[orm.UserORM]:
        query = self.db.query(orm.UserORM).filter(orm.UserORM.deleted_at == None)
        if search:
            query = query.filter(orm.UserORM.email.ilike(f"%{search}%"))
        return query.offset(skip).limit(limit).all()

    def count_users(self, search: Optional[str] = None) -> int:
        query = self.db.query(orm.UserORM).filter(orm.UserORM.deleted_at == None)
        if search:
            query = query.filter(orm.UserORM.email.ilike(f"%{search}%"))
        return query.count()

    # 2. Profile Creation Linkages
    def create_recruiter_profile(self, user_id: str, email: str, company_name: str, password_hash: str) -> orm.RecruiterORM:
        db_rec = orm.RecruiterORM(
            user_id=uuid.UUID(user_id),
            email=email,
            company_name=company_name,
            password_hash=password_hash
        )
        return self.add(db_rec)

    def create_candidate_profile(self, user_id: str, first_name: str, last_name: str, email: str, resume_url: str = "") -> orm.CandidateORM:
        db_cand = orm.CandidateORM(
            user_id=uuid.UUID(user_id),
            first_name=first_name,
            last_name=last_name,
            email=email,
            resume_url=resume_url or f"s3://resumes/placeholder_{user_id}.pdf",
            parsed_skills={}
        )
        return self.add(db_cand)

    # 3. Role Queries
    def get_role_by_name(self, name: str) -> Optional[orm.RoleORM]:
        return self.db.query(orm.RoleORM).filter(orm.RoleORM.name == name.upper()).first()

    # 4. Token Operations
    def create_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> orm.RefreshTokenORM:
        db_token = orm.RefreshTokenORM(
            user_id=uuid.UUID(user_id),
            token_hash=token_hash,
            expires_at=expires_at
        )
        return self.add(db_token)

    def get_refresh_token_by_hash(self, token_hash: str) -> Optional[orm.RefreshTokenORM]:
        return self.db.query(orm.RefreshTokenORM).filter(orm.RefreshTokenORM.token_hash == token_hash).first()

    def revoke_refresh_tokens_for_user(self, user_id: str) -> None:
        """Revokes all refresh tokens for a specific user."""
        self.db.query(orm.RefreshTokenORM).filter(
            orm.RefreshTokenORM.user_id == uuid.UUID(user_id),
            orm.RefreshTokenORM.is_revoked == False
        ).update({"is_revoked": True})
        self.db.commit()

    # Password Reset Tokens
    def create_password_reset_token(self, user_id: str, token_hash: str, expires_at: datetime) -> orm.PasswordResetTokenORM:
        # Revoke previous active tokens to avoid token reuse
        self.db.query(orm.PasswordResetTokenORM).filter(
            orm.PasswordResetTokenORM.user_id == uuid.UUID(user_id),
            orm.PasswordResetTokenORM.is_used == False
        ).update({"is_used": True})
        
        db_token = orm.PasswordResetTokenORM(
            user_id=uuid.UUID(user_id),
            token_hash=token_hash,
            expires_at=expires_at
        )
        return self.add(db_token)

    def get_password_reset_token(self, token_hash: str) -> Optional[orm.PasswordResetTokenORM]:
        return self.db.query(orm.PasswordResetTokenORM).filter(orm.PasswordResetTokenORM.token_hash == token_hash).first()

    # Email Verification Tokens
    def create_verification_token(self, user_id: str, token_hash: str, expires_at: datetime) -> orm.EmailVerificationTokenORM:
        self.db.query(orm.EmailVerificationTokenORM).filter(
            orm.EmailVerificationTokenORM.user_id == uuid.UUID(user_id),
            orm.EmailVerificationTokenORM.is_used == False
        ).update({"is_used": True})

        db_token = orm.EmailVerificationTokenORM(
            user_id=uuid.UUID(user_id),
            token_hash=token_hash,
            expires_at=expires_at
        )
        return self.add(db_token)

    def get_verification_token(self, token_hash: str) -> Optional[orm.EmailVerificationTokenORM]:
        return self.db.query(orm.EmailVerificationTokenORM).filter(orm.EmailVerificationTokenORM.token_hash == token_hash).first()

    # 5. Session Operations
    def create_session(self, user_id: str, session_key: str, ip_address: Optional[str], user_agent: Optional[str], expires_at: datetime) -> orm.UserSessionORM:
        db_session = orm.UserSessionORM(
            user_id=uuid.UUID(user_id),
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        return self.add(db_session)

    def get_session_by_key(self, session_key: str) -> Optional[orm.UserSessionORM]:
        return self.db.query(orm.UserSessionORM).filter(
            orm.UserSessionORM.session_key == session_key,
            orm.UserSessionORM.is_active == True
        ).first()

    def list_active_sessions(self, user_id: str) -> List[orm.UserSessionORM]:
        return self.db.query(orm.UserSessionORM).filter(
            orm.UserSessionORM.user_id == uuid.UUID(user_id),
            orm.UserSessionORM.is_active == True,
            orm.UserSessionORM.expires_at > datetime.now(timezone.utc)
        ).all()

    def deactivate_session(self, session_key: str) -> None:
        self.db.query(orm.UserSessionORM).filter(
            orm.UserSessionORM.session_key == session_key
        ).update({"is_active": False})
        self.db.commit()

    def deactivate_all_user_sessions(self, user_id: str) -> None:
        self.db.query(orm.UserSessionORM).filter(
            orm.UserSessionORM.user_id == uuid.UUID(user_id)
        ).update({"is_active": False})
        self.db.commit()

    # 6. Audit & History Logging
    def log_login_attempt(self, user_id: str, ip_address: Optional[str], user_agent: Optional[str], status: str) -> orm.LoginHistoryORM:
        db_log = orm.LoginHistoryORM(
            user_id=uuid.UUID(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        return self.add(db_log)

    def list_login_history(self, user_id: str, limit: int = 50) -> List[orm.LoginHistoryORM]:
        return self.db.query(orm.LoginHistoryORM).filter(
            orm.LoginHistoryORM.user_id == uuid.UUID(user_id)
        ).order_by(orm.LoginHistoryORM.created_at.desc()).limit(limit).all()

    def create_audit_log(self, user_id: Optional[str], action: str, ip_address: Optional[str], details: dict) -> orm.AuditLogORM:
        db_audit = orm.AuditLogORM(
            user_id=uuid.UUID(user_id) if user_id else None,
            action=action,
            ip_address=ip_address,
            details=details
        )
        return self.add(db_audit)

    def list_audit_logs(self, limit: int = 100, skip: int = 0) -> List[orm.AuditLogORM]:
        return self.db.query(orm.AuditLogORM).order_by(orm.AuditLogORM.created_at.desc()).offset(skip).limit(limit).all()
        
    def count_audit_logs(self) -> int:
        return self.db.query(orm.AuditLogORM).count()
