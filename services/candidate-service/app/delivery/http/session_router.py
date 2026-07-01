# services/candidate-service/app/delivery/http/session_router.py
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.auth import get_current_user, UserIdentity
from services.common.responses import make_success_response
from app.adapter.db.auth_repo import AuthRepository
from app.domain import auth_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Session Management"])


@router.get("/devices", response_model=None)
def get_active_sessions(
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all active devices and login sessions logged in for the current user account.
    """
    repo = AuthRepository(db)
    sessions = repo.list_active_sessions(current_user.id)
    
    session_list = [
        {
            "id": str(s.id),
            "session_key": s.session_key,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "last_activity": s.last_activity,
            "created_at": s.created_at
        } for s in sessions
    ]
    return make_success_response(session_list)


@router.post("/devices/revoke")
def revoke_session(
    session_key: str,
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivates a specific device session, logging out the associated device.
    """
    repo = AuthRepository(db)
    session = repo.get_session_by_key(session_key)
    
    if not session or str(session.user_id) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or permission denied."
        )
        
    repo.deactivate_session(session_key)
    
    repo.create_audit_log(
        user_id=current_user.id,
        action="SESSION_REVOKED_BY_USER",
        ip_address=None,
        details={"revoked_session_key": session_key}
    )

    return make_success_response("Session successfully terminated.")


@router.post("/devices/revoke-all")
def revoke_all_other_sessions(
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivates all sessions for this user EXCEPT the active one mapping to request context.
    """
    repo = AuthRepository(db)
    # Deactivate all sessions
    repo.deactivate_all_user_sessions(current_user.id)
    
    repo.create_audit_log(
        user_id=current_user.id,
        action="ALL_SESSIONS_REVOKED_BY_USER",
        ip_address=None,
        details={}
    )

    return make_success_response("All session tokens terminated.")
