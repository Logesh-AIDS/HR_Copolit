# services/common/auth/jwt_handler.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from jose import JWTError, jwt
from services.common.config import settings
from services.common.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

def create_access_token(
    user_id: str,
    email: str,
    roles: List[str],
    permissions: List[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a secure JWT access token containing identity, roles, and permission claims.
    """
    to_encode = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "permissions": permissions,
        "type": "access"
    }
    
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": int(expire.timestamp())})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        logger.error(f"Failed to generate JWT access token: {e}")
        raise UnauthorizedException("Token generation failed.")


def create_refresh_token(
    user_id: str,
    token_id: str,  # Unique JTI for token tracking and revocation checks
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a secure JWT refresh token for session renewals.
    """
    to_encode = {
        "sub": user_id,
        "jti": token_id,
        "type": "refresh"
    }
    
    # Refresh tokens persist longer (default 7 days)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=7)
    )
    to_encode.update({"exp": int(expire.timestamp())})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        logger.error(f"Failed to generate JWT refresh token: {e}")
        raise UnauthorizedException("Token generation failed.")


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """
    Decodes and validates a JWT token against expiration and signature authenticity.
    Throws UnauthorizedException on errors.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise UnauthorizedException(f"Invalid token type. Expected {expected_type}.")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Attempted to decode an expired token.")
        raise UnauthorizedException("Token has expired.")
    except JWTError as e:
        logger.warning(f"Failed to decode JWT token: {e}")
        raise UnauthorizedException("Invalid authentication credentials.")
