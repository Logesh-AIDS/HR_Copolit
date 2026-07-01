# tests/test_auth.py
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends

from services.common.auth import hash_password, verify_password
from services.common.exceptions import UnauthorizedException, ValidationException
from services.common.email import MockEmailService
from app.adapter.db.auth_repo import AuthRepository
from app.adapter.db import orm
from app.domain import auth_models
from app.domain.services.auth_service import AuthService
from app.domain.services.admin_service import AdminService
from app.delivery.http.auth_router import router as auth_router
from app.delivery.http.profile_router import router as profile_router
from app.delivery.http.admin_router import router as admin_router


@pytest.fixture
def auth_service(db_session):
    repo = AuthRepository(db_session)
    # Seed standard roles in the test DB
    roles = [
        ("d003b5b5-7788-4db8-b5b5-77884db8b5b5", "ADMINISTRATOR"),
        ("e114c6c6-8899-5ec9-c6c6-88995ec9c6c6", "RECRUITER"),
        ("f225d7d7-99aa-6fd0-d7d7-99aa6fd0d7d7", "CANDIDATE"),
        ("a336e8e8-00bb-7fe1-e8e8-00bb7fe1e8e8", "HIRING_MANAGER")
    ]
    for rid, rname in roles:
        role = orm.RoleORM(id=uuid.UUID(rid), name=rname)
        db_session.add(role)
    db_session.commit()

    email = MockEmailService()
    return AuthService(repo, email)


@pytest.fixture
def admin_service(db_session):
    repo = AuthRepository(db_session)
    return AdminService(repo)


def test_password_cryptography():
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_registration_and_verification(auth_service):
    payload = auth_models.UserRegister(
        email="test_candidate@example.com",
        password="Password123!",
        role="CANDIDATE",
        first_name="Test",
        last_name="Candidate"
    )
    user = auth_service.register_user(payload)
    
    assert user.email == "test_candidate@example.com"
    assert user.is_verified is False
    assert user.is_active is True
    
    # Check duplicate registration prevention
    with pytest.raises(ValidationException) as exc:
        auth_service.register_user(payload)
    assert "already registered" in str(exc.value)


def test_failed_login_lockout(auth_service):
    # Register user
    reg_payload = auth_models.UserRegister(
        email="lockme@example.com",
        password="Password123!",
        role="CANDIDATE"
    )
    auth_service.register_user(reg_payload)

    # In-memory mock details
    login_payload = auth_models.UserLogin(
        email="lockme@example.com",
        password="WrongPassword1!"
    )

    # 4 Failed attempts
    for _ in range(4):
        with pytest.raises(UnauthorizedException):
            auth_service.login_user(login_payload, "127.0.0.1", "test-agent")

    # 5th attempt locks the account, returns invalid password still
    with pytest.raises(UnauthorizedException):
        auth_service.login_user(login_payload, "127.0.0.1", "test-agent")

    # 6th attempt blocks access with lockout status message
    with pytest.raises(UnauthorizedException) as exc:
        auth_service.login_user(login_payload, "127.0.0.1", "test-agent")
    assert "locked" in str(exc.value).lower()


def test_refresh_token_rotation_and_replay_detection(auth_service):
    # Register and verify
    reg_payload = auth_models.UserRegister(
        email="rotate@example.com",
        password="Password123!",
        role="CANDIDATE"
    )
    user = auth_service.register_user(reg_payload)
    user.is_verified = True
    auth_service.repo.commit()

    # Login
    login_payload = auth_models.UserLogin(email="rotate@example.com", password="Password123!")
    tokens, _ = auth_service.login_user(login_payload, "127.0.0.1", "test-agent")
    
    first_refresh = tokens.refresh_token

    # Perform first refresh (Success)
    new_tokens = auth_service.refresh_session_tokens(first_refresh)
    assert new_tokens.refresh_token != first_refresh

    # Attempt to REUSE first_refresh token (Replay Attack)
    # This should trigger RTR panic, revoke all tokens, and fail access
    with pytest.raises(UnauthorizedException) as exc:
        auth_service.refresh_session_tokens(first_refresh)
    assert "revoked" in str(exc.value).lower()


def test_admin_suspend_user(auth_service, admin_service):
    # Register recruiter
    reg_payload = auth_models.UserRegister(
        email="recruit@example.com",
        password="Password123!",
        role="RECRUITER",
        company_name="Acme Corp"
    )
    user = auth_service.register_user(reg_payload)
    user.is_verified = True
    
    # Register admin
    admin_payload = auth_models.UserRegister(
        email="admin@example.com",
        password="Password123!",
        role="ADMINISTRATOR"
    )
    admin = auth_service.register_user(admin_payload)
    
    # Suspend
    admin_service.suspend_user(str(user.id), str(admin.id))
    
    # Attempt login on suspended account
    login_payload = auth_models.UserLogin(email="recruit@example.com", password="Password123!")
    with pytest.raises(UnauthorizedException) as exc:
        auth_service.login_user(login_payload, "127.0.0.1", "test-agent")
    assert "deactivated" in str(exc.value).lower()
