# services/candidate-service/app/delivery/http/admin_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity, RequireRole
from services.common.responses import make_success_response, make_paginated_response
from app.adapter.db.auth_repo import AuthRepository
from app.domain import auth_models
from app.domain.services.admin_service import AdminService

logger = logging.getLogger(__name__)

# Enforce ADMINISTRATOR role validation globally on this router
router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(RequireRole(["ADMINISTRATOR"]))]
)

def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    repo = AuthRepository(db)
    return AdminService(repo)


@router.get("/users")
def get_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    service: AdminService = Depends(get_admin_service)
):
    """
    Lists users with pagination and email search parameters.
    """
    users, total = service.list_users(skip=skip, limit=limit, search=search)
    user_list = [
        {
            "id": str(u.id),
            "email": u.email,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "roles": [r.name for r in u.roles],
            "created_at": u.created_at
        } for u in users
    ]
    return make_paginated_response(user_list, total, skip, limit)


@router.post("/suspend")
def suspend_user(
    user_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Suspends a user account, terminating all active refresh tokens and sessions.
    """
    service.suspend_user(user_id, current_user.id)
    return make_success_response("User suspended successfully.")


@router.post("/activate")
def activate_user(
    user_id: str,
    current_user: UserIdentity = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Activates a suspended user account, restoring login capabilities.
    """
    service.activate_user(user_id, current_user.id)
    return make_success_response("User activated successfully.")


@router.post("/assign-role")
def assign_role(
    payload: auth_models.RoleAssignPayload,
    current_user: UserIdentity = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Assigns a specific role (e.g. ADMINISTRATOR, RECRUITER, CANDIDATE, HIRING_MANAGER) to a user.
    """
    service.assign_role_to_user(payload.user_id, payload.role_name, current_user.id)
    return make_success_response(f"Role '{payload.role_name}' assigned successfully.")


@router.post("/remove-role")
def remove_role(
    payload: auth_models.RoleAssignPayload,
    current_user: UserIdentity = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Removes a specific role assignment from a user.
    """
    service.remove_role_from_user(payload.user_id, payload.role_name, current_user.id)
    return make_success_response(f"Role '{payload.role_name}' removed successfully.")


@router.post("/reset-user-password")
def reset_user_password(
    user_id: str,
    payload: auth_models.ResetPasswordRequest,
    current_user: UserIdentity = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Forcibly overrides a user's password, terminating all active logins for the user.
    """
    service.admin_reset_password(user_id, payload.new_password, current_user.id)
    return make_success_response("User password reset successfully. Sessions invalidated.")


@router.get("/audit-logs")
def get_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    service: AdminService = Depends(get_admin_service)
):
    """
    Lists system-wide security audit logs chronologically.
    """
    logs, total = service.list_audit_logs(skip=skip, limit=limit)
    log_list = [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "ip_address": l.ip_address,
            "details": l.details,
            "created_at": l.created_at
        } for l in logs
    ]
    return make_paginated_response(log_list, total, skip, limit)


@router.get("/user-history/{user_id}")
def get_user_login_history(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    service: AdminService = Depends(get_admin_service)
):
    """
    Lists the login history log for a specific user.
    """
    history = service.view_user_login_history(user_id, limit=limit)
    history_list = [
        {
            "id": str(h.id),
            "ip_address": h.ip_address,
            "user_agent": h.user_agent,
            "status": h.status,
            "created_at": h.created_at
        } for h in history
    ]
    return make_success_response(history_list)
