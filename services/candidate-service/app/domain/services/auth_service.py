# services/candidate-service/app/domain/services/auth_service.py
import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from services.common.auth import (
    hash_password, verify_password,
    validate_password_strength, create_access_token, create_refresh_token
)
from services.common.email import EmailService
from services.common.exceptions import UnauthorizedException, ValidationException, NotFoundException
from app.adapter.db.auth_repo import AuthRepository
from app.adapter.db import orm
from app.domain import auth_models

logger = logging.getLogger(__name__)

class AuthService:
    """
    Business service coordinator executing clean authentication, verification, and credentials rotation logic.
    """
    def __init__(self, repo: AuthRepository, email_service: EmailService):
        self.repo = repo
        self.email_service = email_service

    def _hash_token(self, token: str) -> str:
        """Helper hashing token string for database storage encryption."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _is_expired(self, dt: datetime) -> bool:
        """Helper verifying if a database datetime is in the past, supporting naive and aware comparisons."""
        if dt.tzinfo is not None:
            return dt < datetime.now(timezone.utc)
        return dt < datetime.now(timezone.utc).replace(tzinfo=None)

    def _get_lockout_seconds(self, locked_until: datetime) -> int:
        """Helper calculating duration until lockout expires in a timezone-independent manner."""
        if locked_until.tzinfo is not None:
            return int((locked_until - datetime.now(timezone.utc)).total_seconds())
        return int((locked_until - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())

    # 1. User Registration
    def register_user(self, payload: auth_models.UserRegister) -> orm.UserORM:
        logger.info(f"Registering new user: {payload.email}")
        
        # Check for duplicate user
        existing_user = self.repo.get_user_by_email(payload.email)
        if existing_user:
            raise ValidationException("Email address already registered.")

        # Check password complexity constraints
        validate_password_strength(payload.password)

        # Hash password and create base credentials
        hashed_pwd = hash_password(payload.password)
        db_user = orm.UserORM(
            email=payload.email,
            password_hash=hashed_pwd,
            is_active=True,
            is_verified=False
        )
        db_user = self.repo.add(db_user)

        # Map role profile details based on requested role
        role_name = payload.role.upper()
        if role_name not in {"CANDIDATE", "RECRUITER"}:
            role_name = "CANDIDATE"

        db_role = self.repo.get_role_by_name(role_name)
        if not db_role:
            # Fallback seed role if missing
            db_role = orm.RoleORM(name=role_name)
            db_role = self.repo.add(db_role)

        # Assign Role
        db_user.roles.append(db_role)
        self.repo.commit()

        # Create Profile
        if role_name == "RECRUITER":
            if not payload.company_name:
                raise ValidationException("Company name is required for recruiters.")
            self.repo.create_recruiter_profile(
                user_id=str(db_user.id),
                email=payload.email,
                company_name=payload.company_name,
                password_hash=hashed_pwd
            )
        else:
            self.repo.create_candidate_profile(
                user_id=str(db_user.id),
                first_name=payload.first_name or "Applicant",
                last_name=payload.last_name or "User",
                email=payload.email
            )

        # Generate Email Verification Token
        verify_token = str(uuid.uuid4())
        hashed_token = self._hash_token(verify_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        self.repo.create_verification_token(
            user_id=str(db_user.id),
            token_hash=hashed_token,
            expires_at=expires_at
        )

        # Audit and Notify
        self.repo.create_audit_log(
            user_id=str(db_user.id),
            action="USER_REGISTERED",
            ip_address=None,
            details={"email": payload.email, "role": role_name}
        )
        
        # Send mail in background
        self.email_service.send_verification_email(payload.email, verify_token)
        
        return db_user

    # 2. Login Logic
    def login_user(
        self,
        payload: auth_models.UserLogin,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> Tuple[auth_models.TokenResponse, str]:
        """
        Validates login, handles account lockouts, and generates JWT/sessions on success.
        """
        db_user = self.repo.get_user_by_email(payload.email)
        if not db_user:
            raise UnauthorizedException("Invalid email or password.")

        # Check suspension
        if not db_user.is_active:
            raise UnauthorizedException("Your account is deactivated. Contact support.")

        # Check lockout
        if db_user.locked_until and not self._is_expired(db_user.locked_until):
            locked_seconds = self._get_lockout_seconds(db_user.locked_until)
            raise UnauthorizedException(
                f"Account is temporarily locked. Try again in {locked_seconds // 60 + 1} minutes."
            )

        # Verify password
        if verify_password(payload.password, db_user.password_hash):
            # Login successful
            db_user.failed_login_attempts = 0
            db_user.locked_until = None
            self.repo.commit()

            # Map user roles and permissions
            roles = [role.name for role in db_user.roles]
            permissions = []
            for role in db_user.roles:
                permissions.extend([perm.name for perm in role.permissions])
            permissions = list(set(permissions))  # De-duplicate

            # Generate tokens
            access_token = create_access_token(
                user_id=str(db_user.id),
                email=db_user.email,
                roles=roles,
                permissions=permissions
            )
            
            # Generate Refresh Token and track JTI
            refresh_jti = str(uuid.uuid4())
            refresh_token = create_refresh_token(user_id=str(db_user.id), token_id=refresh_jti)
            hashed_refresh = self._hash_token(refresh_token)
            
            # Save Refresh Token
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            self.repo.create_refresh_token(
                user_id=str(db_user.id),
                token_hash=hashed_refresh,
                expires_at=expires_at
            )

            # Create User Session
            session_key = str(uuid.uuid4())
            self.repo.create_session(
                user_id=str(db_user.id),
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )

            # Audit logging
            self.repo.log_login_attempt(str(db_user.id), ip_address, user_agent, "SUCCESS")
            self.repo.create_audit_log(
                user_id=str(db_user.id),
                action="USER_LOGGED_IN",
                ip_address=ip_address,
                details={"ip": ip_address}
            )

            return auth_models.TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token
            ), session_key

        else:
            # Login failed. Track brute force metrics
            db_user.failed_login_attempts += 1
            if db_user.failed_login_attempts >= 5:
                # 15 minutes lockout
                db_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                logger.warning(f"Brute force protection triggered. User {db_user.email} locked for 15 minutes.")
                self.repo.log_login_attempt(str(db_user.id), ip_address, user_agent, "LOCKED")
                self.repo.create_audit_log(
                    user_id=str(db_user.id),
                    action="ACCOUNT_LOCKED",
                    ip_address=ip_address,
                    details={"attempts": db_user.failed_login_attempts}
                )
                self.email_service.send_security_alert(
                    db_user.email,
                    "Too many failed login attempts. Your account has been locked for 15 minutes."
                )
            else:
                self.repo.log_login_attempt(str(db_user.id), ip_address, user_agent, "FAILED_PASSWORD")
            
            self.repo.commit()
            raise UnauthorizedException("Invalid email or password.")

    # 3. Refresh Token Rotation (RTR)
    def refresh_session_tokens(self, refresh_jwt: str) -> auth_models.TokenResponse:
        """
        Executes token rotation, detecting token theft and anomalies.
        """
        from services.common.auth.jwt_handler import decode_token
        
        # Decode and inspect token JTI
        payload = decode_token(refresh_jwt, expected_type="refresh")
        user_id = payload.get("sub")
        token_jti = payload.get("jti")
        
        if not user_id or not token_jti:
            raise UnauthorizedException("Malformed credentials.")

        # Find token in DB by hash
        hashed_current = self._hash_token(refresh_jwt)
        db_token = self.repo.get_refresh_token_by_hash(hashed_current)

        if not db_token:
            raise UnauthorizedException("Invalid session refresh credentials.")

        # Detect Replay Attacks (Breach Mitigation)
        if db_token.is_revoked:
            logger.critical(
                f"REPLAY ATTACK DETECTED for user {user_id}. Revoked refresh token reused! "
                f"Revoking all active tokens to block compromise."
            )
            # Instantly log out user from ALL active terminals
            self.repo.revoke_refresh_tokens_for_user(user_id)
            self.repo.deactivate_all_user_sessions(user_id)
            
            # Send critical alert
            db_user = self.repo.get_user_by_id(user_id)
            if db_user:
                self.email_service.send_security_alert(
                    db_user.email,
                    "Warning: We detected abnormal login renewal attempts. All active sessions have been terminated."
                )
            raise UnauthorizedException("Session revoked due to security validation failure.")

        # Verify expiration
        if self._is_expired(db_token.expires_at):
            db_token.is_revoked = True
            self.repo.commit()
            raise UnauthorizedException("Refresh session expired.")

        # Execute Rotation (RTR)
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user or not db_user.is_active:
            raise UnauthorizedException("User profile is suspended.")

        # Revoke old refresh token
        db_token.is_revoked = True
        self.repo.commit()

        # Build new access and refresh tokens
        roles = [role.name for role in db_user.roles]
        permissions = []
        for role in db_user.roles:
            permissions.extend([perm.name for perm in role.permissions])
        permissions = list(set(permissions))

        new_access = create_access_token(
            user_id=user_id,
            email=db_user.email,
            roles=roles,
            permissions=permissions
        )
        
        new_jti = str(uuid.uuid4())
        new_refresh = create_refresh_token(user_id=user_id, token_id=new_jti)
        hashed_new = self._hash_token(new_refresh)

        # Save new refresh token, linking rotation lineage
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        db_new_token = orm.RefreshTokenORM(
            user_id=uuid.UUID(user_id),
            token_hash=hashed_new,
            expires_at=expires_at
        )
        self.repo.add(db_new_token)
        db_token.replaced_by = db_new_token.id
        self.repo.commit()

        return auth_models.TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh
        )

    # 4. Verification Processes
    def verify_email(self, token: str) -> None:
        hashed_token = self._hash_token(token)
        db_token = self.repo.get_verification_token(hashed_token)
        
        if not db_token or db_token.is_used:
            raise ValidationException("Invalid or already used verification link.")
            
        if self._is_expired(db_token.expires_at):
            raise ValidationException("Verification link has expired.")

        # Mark token as used
        db_token.is_used = True
        
        # Verify user
        db_user = self.repo.get_user_by_id(str(db_token.user_id))
        if not db_user:
            raise NotFoundException("User not found.")
            
        db_user.is_verified = True
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=str(db_user.id),
            action="EMAIL_VERIFIED",
            ip_address=None,
            details={}
        )
        
        # Send Welcome
        self.email_service.send_welcome_email(db_user.email, db_user.email.split("@")[0])

    def resend_verification(self, email: str) -> None:
        db_user = self.repo.get_user_by_email(email)
        if not db_user:
            return  # Prevent account enumeration leaks by exiting silently
            
        if db_user.is_verified:
            raise ValidationException("Email is already verified.")

        # Create new verification token
        verify_token = str(uuid.uuid4())
        hashed_token = self._hash_token(verify_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        self.repo.create_verification_token(
            user_id=str(db_user.id),
            token_hash=hashed_token,
            expires_at=expires_at
        )

        self.email_service.send_verification_email(db_user.email, verify_token)
        logger.info(f"Verification email resent to: {email}")

    # 5. Password Reset Flows
    def request_password_reset(self, email: str) -> None:
        db_user = self.repo.get_user_by_email(email)
        if not db_user:
            return  # Silent exit to block credential probing

        reset_token = str(uuid.uuid4())
        hashed_token = self._hash_token(reset_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        self.repo.create_password_reset_token(
            user_id=str(db_user.id),
            token_hash=hashed_token,
            expires_at=expires_at
        )

        self.email_service.send_forgot_password_email(db_user.email, reset_token)
        
        self.repo.create_audit_log(
            user_id=str(db_user.id),
            action="PASSWORD_RESET_REQUESTED",
            ip_address=None,
            details={}
        )

    def reset_password(self, payload: auth_models.ResetPasswordRequest) -> None:
        hashed_token = self._hash_token(payload.token)
        db_token = self.repo.get_password_reset_token(hashed_token)
        
        if not db_token or db_token.is_used:
            raise ValidationException("Invalid or already used password reset link.")
            
        if self._is_expired(db_token.expires_at):
            raise ValidationException("Reset link has expired.")

        validate_password_strength(payload.new_password)
        hashed_new_pwd = hash_password(payload.new_password)

        db_user = self.repo.get_user_by_id(str(db_token.user_id))
        if not db_user:
            raise NotFoundException("User not found.")

        # Check if identical to old password (history logic)
        if verify_password(payload.new_password, db_user.password_hash):
            raise ValidationException("New password cannot be the same as your old password.")

        # Apply password reset
        db_user.password_hash = hashed_new_pwd
        db_token.is_used = True
        
        # Kill active sessions and tokens for security
        self.repo.revoke_refresh_tokens_for_user(str(db_user.id))
        self.repo.deactivate_all_user_sessions(str(db_user.id))
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=str(db_user.id),
            action="PASSWORD_RESET_COMPLETED",
            ip_address=None,
            details={}
        )
        
        self.email_service.send_security_alert(db_user.email, "Your password has been successfully reset.")

    # 6. Change Password Flow
    def change_password(self, user_id: str, payload: auth_models.ChangePasswordRequest) -> None:
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found.")

        # Verify old password
        if not verify_password(payload.old_password, db_user.password_hash):
            raise ValidationException("Invalid current password.")

        validate_password_strength(payload.new_password)
        
        # Check against history
        if verify_password(payload.new_password, db_user.password_hash):
            raise ValidationException("New password cannot be the same as your current password.")

        hashed_pwd = hash_password(payload.new_password)
        db_user.password_hash = hashed_pwd
        
        # Purge active sessions/refresh tokens to verify logout everywhere
        self.repo.revoke_refresh_tokens_for_user(user_id)
        self.repo.deactivate_all_user_sessions(user_id)
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=user_id,
            action="PASSWORD_CHANGED",
            ip_address=None,
            details={}
        )
        self.email_service.send_security_alert(db_user.email, "Your password has been changed. Sessions revoked.")

    # 7. Logout Execution
    def logout_user(self, refresh_jwt: Optional[str], session_key: Optional[str]) -> None:
        if refresh_jwt:
            hashed_current = self._hash_token(refresh_jwt)
            db_token = self.repo.get_refresh_token_by_hash(hashed_current)
            if db_token:
                db_token.is_revoked = True
                
        if session_key:
            self.repo.deactivate_session(session_key)
            
        self.repo.commit()
