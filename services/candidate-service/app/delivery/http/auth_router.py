# services/candidate-service/app/delivery/http/auth_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Response, Request, status
from sqlalchemy.orm import Session

from services.common.database import get_db
from services.common.responses import make_success_response
from services.common.email import MockEmailService
from app.adapter.db.auth_repo import AuthRepository
from app.domain import auth_models
from app.domain.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = AuthRepository(db)
    email_service = MockEmailService()  # Interchangeable provider dependency
    return AuthService(repo, email_service)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: auth_models.UserRegister, service: AuthService = Depends(get_auth_service)):
    """
    Registers a new recruiter or candidate account, seeds profile, and sends verification email.
    """
    user = service.register_user(payload)
    return make_success_response({
        "user_id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified
    })


@router.post("/login")
def login(
    payload: auth_models.UserLogin,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """
    Validates user credentials. If valid, generates JWT access/refresh tokens and user session.
    Sets secure HttpOnly cookies on the client.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    tokens, session_key = service.login_user(payload, ip_address, user_agent)
    
    # Set Secure HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60, # 15 minutes
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60, # 7 days
        path="/"
    )
    response.set_cookie(
        key="session_key",
        value=session_key,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    return make_success_response({
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "session_key": session_key
    })


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """
    Renews session access and refresh tokens under Refresh Token Rotation (RTR).
    Reads refresh token from header or cookie, and returns new tokens inside cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        # Fallback to authorization header if cookies are empty
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            refresh_token = auth_header[7:]
            
    if not refresh_token:
        from services.common.exceptions import UnauthorizedException
        raise UnauthorizedException("Session refresh token missing. Log in again.")
        
    tokens = service.refresh_session_tokens(refresh_token)
    
    # Set the updated tokens in cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    return make_success_response({
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token
    })


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service)
):
    """
    Invalidates current session tokens in database and deletes HTTP-only client cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    session_key = request.cookies.get("session_key")
    
    service.logout_user(refresh_token, session_key)
    
    # Delete cookies on client browser
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    response.delete_cookie(key="session_key", path="/")
    
    return make_success_response("Logged out successfully.")


@router.get("/verify-email")
def verify_email(token: str, service: AuthService = Depends(get_auth_service)):
    """
    Validates verification link token to activate email verification status.
    """
    service.verify_email(token)
    return make_success_response("Email verified successfully.")


@router.post("/resend-verification")
def resend_verification(email: str, service: AuthService = Depends(get_auth_service)):
    """
    Re-sends activation/verification email if account is not yet verified.
    """
    service.resend_verification(email)
    return make_success_response("If the email exists, a verification link has been resent.")


@router.post("/forgot-password")
def forgot_password(payload: auth_models.ForgotPasswordRequest, service: AuthService = Depends(get_auth_service)):
    """
    Sends password recovery email containing secure token link.
    """
    service.request_password_reset(payload.email)
    return make_success_response("If the email exists, a password reset link has been dispatched.")


@router.post("/reset-password")
def reset_password(payload: auth_models.ResetPasswordRequest, service: AuthService = Depends(get_auth_service)):
    """
    Ingests reset token and replaces user password with new credentials.
    """
    service.reset_password(payload)
    return make_success_response("Password reset successfully. Please log in.")
