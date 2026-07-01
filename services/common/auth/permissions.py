# services/common/auth/permissions.py
import logging
from typing import List, Optional
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from services.common.auth.jwt_handler import decode_token
from services.common.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

# Bearer scheme configuration (but we keep it optional to allow fallback to Cookies!)
bearer_scheme = HTTPBearer(auto_error=False)

class UserIdentity(BaseModel):
    id: str
    email: str
    roles: List[str]
    permissions: List[str]


def get_current_user(
    request: Request,
    token_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> UserIdentity:
    """
    FastAPI dependency resolving the current user from headers or secure cookies.
    """
    token: Optional[str] = None
    
    # 1. Inspect Authorization Header
    if token_credentials:
        token = token_credentials.credentials
        
    # 2. Fallback: Inspect secure HTTP-only cookie store
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        raise UnauthorizedException("Authentication token is missing. Please log in.")
        
    # Decode access token
    payload = decode_token(token, expected_type="access")
    
    user_id = payload.get("sub")
    email = payload.get("email")
    roles = payload.get("roles", [])
    permissions = payload.get("permissions", [])
    
    if not user_id or not email:
        raise UnauthorizedException("Invalid token payload. Identity claims missing.")
        
    return UserIdentity(
        id=user_id,
        email=email,
        roles=roles,
        permissions=permissions
    )


class RequireRole:
    """
     Fast security filter restricting routes to users holding specified roles.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserIdentity = Depends(get_current_user)) -> None:
        # Check if user holds any of the allowed roles
        has_role = any(role in self.allowed_roles for role in current_user.roles)
        
        # Grant access to Administrators unconditionally (Superuser bypass pattern)
        if "ADMINISTRATOR" in current_user.roles:
            has_role = True
            
        if not has_role:
            logger.warning(
                f"Unauthorized role access attempt by user {current_user.id} "
                f"with roles {current_user.roles}. Required one of: {self.allowed_roles}"
            )
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have the required role privileges."
            )


class RequirePermission:
    """
    Fast security filter restricting routes to users holding specific permissions.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: UserIdentity = Depends(get_current_user)) -> None:
        # Check if user holds the exact permission
        has_permission = self.required_permission in current_user.permissions
        
        # Administrators bypass permissions validations
        if "ADMINISTRATOR" in current_user.roles:
            has_permission = True
            
        if not has_permission:
            logger.warning(
                f"Unauthorized permission access attempt by user {current_user.id}. "
                f"Required permission: {self.required_permission}"
            )
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing required permission: {self.required_permission}"
            )
