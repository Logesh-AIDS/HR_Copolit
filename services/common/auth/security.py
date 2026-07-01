# services/common/auth/security.py
import re
import bcrypt
from typing import List
from services.common.exceptions import ValidationException

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using BCrypt with 12 salt rounds.
    """
    # bcrypt requires bytes
    passwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(passwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored BCrypt hash.
    """
    passwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(passwd_bytes, hashed_bytes)
    except Exception:
        return False

def validate_password_strength(password: str) -> None:
    """
    Validates password strength constraints (minimum 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special).
    Throws ValidationException if constraints are not met.
    """
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationException("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationException("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationException("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationException("Password must contain at least one special character.")

def validate_password_history(new_password: str, hashed_history: List[str]) -> None:
    """
    Validates that a new password does not match any of the previously used hashed passwords.
    """
    for old_hash in hashed_history:
        if verify_password(new_password, old_hash):
            raise ValidationException("New password cannot be the same as any of your previous passwords.")
