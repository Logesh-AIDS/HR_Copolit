# services/candidate-service/app/domain/services/admin_service.py
import logging
from typing import List, Optional, Tuple
from app.adapter.db.auth_repo import AuthRepository
from app.adapter.db import orm
from services.common.exceptions import NotFoundException, ValidationException
from services.common.auth import hash_password, validate_password_strength

logger = logging.getLogger(__name__)

class AdminService:
    """
    Administrative management service for user, role, permission, audit log, and lockout configurations.
    """
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def list_users(self, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> Tuple[List[orm.UserORM], int]:
        users = self.repo.list_users(skip=skip, limit=limit, search=search)
        total = self.repo.count_users(search=search)
        return users, total

    def suspend_user(self, user_id: str, admin_user_id: str) -> None:
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found.")
            
        if db_user.id == admin_user_id:
            raise ValidationException("You cannot suspend your own account.")

        db_user.is_active = False
        
        # Invalidate all sessions/tokens to log them out immediately
        self.repo.revoke_refresh_tokens_for_user(user_id)
        self.repo.deactivate_all_user_sessions(user_id)
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=admin_user_id,
            action="USER_SUSPENDED",
            ip_address=None,
            details={"suspended_user_id": user_id}
        )
        logger.info(f"Admin {admin_user_id} suspended user {user_id}")

    def activate_user(self, user_id: str, admin_user_id: str) -> None:
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found.")

        db_user.is_active = True
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=admin_user_id,
            action="USER_ACTIVATED",
            ip_address=None,
            details={"activated_user_id": user_id}
        )
        logger.info(f"Admin {admin_user_id} activated user {user_id}")

    def assign_role_to_user(self, user_id: str, role_name: str, admin_user_id: str) -> None:
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found.")

        db_role = self.repo.get_role_by_name(role_name)
        if not db_role:
            raise NotFoundException(f"Role '{role_name}' does not exist.")

        if db_role in db_user.roles:
            raise ValidationException("User already has this role.")

        db_user.roles.append(db_role)
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=admin_user_id,
            action="ROLE_ASSIGNED",
            ip_address=None,
            details={"assigned_role": role_name, "target_user_id": user_id}
        )
        logger.info(f"Admin {admin_user_id} assigned role {role_name} to user {user_id}")

    def remove_role_from_user(self, user_id: str, role_name: str, admin_user_id: str) -> None:
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found.")

        db_role = self.repo.get_role_by_name(role_name)
        if not db_role:
            raise NotFoundException(f"Role '{role_name}' does not exist.")

        if db_role not in db_user.roles:
            raise ValidationException("User does not have this role.")

        db_user.roles.remove(db_role)
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=admin_user_id,
            action="ROLE_REMOVED",
            ip_address=None,
            details={"removed_role": role_name, "target_user_id": user_id}
        )
        logger.info(f"Admin {admin_user_id} removed role {role_name} from user {user_id}")

    def admin_reset_password(self, user_id: str, new_password: str, admin_user_id: str) -> None:
        db_user = self.repo.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found.")

        validate_password_strength(new_password)
        hashed_pwd = hash_password(new_password)
        
        db_user.password_hash = hashed_pwd
        
        # Terminate active user sessions to force relogin
        self.repo.revoke_refresh_tokens_for_user(user_id)
        self.repo.deactivate_all_user_sessions(user_id)
        self.repo.commit()

        self.repo.create_audit_log(
            user_id=admin_user_id,
            action="USER_PASSWORD_RESET_BY_ADMIN",
            ip_address=None,
            details={"target_user_id": user_id}
        )
        logger.info(f"Admin {admin_user_id} forced password reset for user {user_id}")

    def list_audit_logs(self, skip: int = 0, limit: int = 100) -> Tuple[List[orm.AuditLogORM], int]:
        logs = self.repo.list_audit_logs(limit=limit, skip=skip)
        total = self.repo.count_audit_logs()
        return logs, total

    def view_user_login_history(self, user_id: str, limit: int = 50) -> List[orm.LoginHistoryORM]:
        return self.repo.list_login_history(user_id=user_id, limit=limit)
