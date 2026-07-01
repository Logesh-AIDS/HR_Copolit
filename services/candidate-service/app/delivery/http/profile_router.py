# services/candidate-service/app/delivery/http/profile_router.py
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity
from services.common.responses import make_success_response
from services.common.email import MockEmailService
from app.adapter.db.auth_repo import AuthRepository
from app.domain import auth_models
from app.domain.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile Management"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = AuthRepository(db)
    email_service = MockEmailService()
    return AuthService(repo, email_service)


@router.get("/me", response_model=None)
def get_me(
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full identity info and business profiles associated with the active user context.
    """
    repo = AuthRepository(db)
    db_user = repo.get_user_by_id(current_user.id)
    if not db_user:
        from services.common.exceptions import UnauthorizedException
        raise UnauthorizedException("Session invalid. User profile missing.")
        
    profile_data = {}
    if "RECRUITER" in current_user.roles and db_user.recruiter_profile:
        profile_data = {
            "profile_type": "RECRUITER",
            "company_name": db_user.recruiter_profile.company_name
        }
    elif "CANDIDATE" in current_user.roles and db_user.candidate_profile:
        profile_data = {
            "profile_type": "CANDIDATE",
            "first_name": db_user.candidate_profile.first_name,
            "last_name": db_user.candidate_profile.last_name,
            "resume_url": db_user.candidate_profile.resume_url,
            "skills": db_user.candidate_profile.parsed_skills
        }
        
    return make_success_response({
        "id": str(db_user.id),
        "email": db_user.email,
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
        "profile": profile_data
    })


@router.patch("/update")
def update_profile(
    payload: auth_models.UpdateProfileRequest,
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates profile fields (names or company details) linked to user account.
    """
    repo = AuthRepository(db)
    db_user = repo.get_user_by_id(current_user.id)
    if not db_user:
        from services.common.exceptions import UnauthorizedException
        raise UnauthorizedException("User profile not found.")

    updated_fields = {}
    if "RECRUITER" in current_user.roles and db_user.recruiter_profile:
        if payload.company_name:
            db_user.recruiter_profile.company_name = payload.company_name
            updated_fields["company_name"] = payload.company_name
    elif "CANDIDATE" in current_user.roles and db_user.candidate_profile:
        if payload.first_name:
            db_user.candidate_profile.first_name = payload.first_name
            updated_fields["first_name"] = payload.first_name
        if payload.last_name:
            db_user.candidate_profile.last_name = payload.last_name
            updated_fields["last_name"] = payload.last_name
            
    repo.commit()

    repo.create_audit_log(
        user_id=current_user.id,
        action="PROFILE_UPDATED",
        ip_address=None,
        details=updated_fields
    )

    return make_success_response("Profile updated successfully.")


@router.post("/change-password")
def change_password(
    payload: auth_models.ChangePasswordRequest,
    current_user: UserIdentity = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """
    Changes account password. Triggers validation and invalidates all other active sessions.
    """
    service.change_password(current_user.id, payload)
    return make_success_response("Password updated successfully. Other active sessions revoked.")


@router.post("/deactivate")
def deactivate_account(
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Self-deactivates the user account, revoking active sessions and blocking access.
    """
    repo = AuthRepository(db)
    db_user = repo.get_user_by_id(current_user.id)
    if not db_user:
        from services.common.exceptions import UnauthorizedException
        raise UnauthorizedException("User profile not found.")

    db_user.is_active = False
    
    # Invalidate session states
    repo.revoke_refresh_tokens_for_user(current_user.id)
    repo.deactivate_all_user_sessions(current_user.id)
    repo.commit()

    repo.create_audit_log(
        user_id=current_user.id,
        action="ACCOUNT_DEACTIVATED_BY_USER",
        ip_address=None,
        details={}
    )

    return make_success_response("Account deactivated successfully.")


@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_account(
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft-deletes the user account by setting the `deleted_at` timestamp.
    """
    repo = AuthRepository(db)
    db_user = repo.get_user_by_id(current_user.id)
    if not db_user:
        from services.common.exceptions import UnauthorizedException
        raise UnauthorizedException("User profile not found.")

    from datetime import datetime, timezone
    db_user.deleted_at = datetime.now(timezone.utc)
    db_user.is_active = False
    
    # Clean active sessions
    repo.revoke_refresh_tokens_for_user(current_user.id)
    repo.deactivate_all_user_sessions(current_user.id)
    repo.commit()

    repo.create_audit_log(
        user_id=current_user.id,
        action="ACCOUNT_SOFT_DELETED",
        ip_address=None,
        details={}
    )

    return make_success_response("Account successfully deleted.")
