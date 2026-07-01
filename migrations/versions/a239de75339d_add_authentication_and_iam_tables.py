"""Add authentication and IAM tables

Revision ID: a239de75339d
Revises: 3b26f0f5deda
Create Date: 2026-07-01 13:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a239de75339d'
down_revision: Union[str, Sequence[str], None] = '3b26f0f5deda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create central users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_deleted', 'users', ['deleted_at'], unique=False)

    # 2. Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_roles_name', 'roles', ['name'], unique=True)

    # 3. Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_permissions_name', 'permissions', ['name'], unique=True)

    # 4. Create role_permissions join table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('permission_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 5. Create user_roles join table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # 6. Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('replaced_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['replaced_by'], ['refresh_tokens.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('idx_refresh_tokens_hash', 'refresh_tokens', ['token_hash'], unique=True)

    # 7. Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('idx_pwd_reset_hash', 'password_reset_tokens', ['token_hash'], unique=True)

    # 8. Create email_verification_tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('idx_email_verify_hash', 'email_verification_tokens', ['token_hash'], unique=True)

    # 9. Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_key', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_key')
    )
    op.create_index('idx_sessions_key', 'user_sessions', ['session_key'], unique=True)

    # 10. Create login_history table
    op.create_table(
        'login_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_login_history_user', 'login_history', ['user_id'], unique=False)

    # 11. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)

    # 12. Link recruiters and candidates to users table
    op.add_column('recruiters', sa.Column('user_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_recruiters_user', 'recruiters', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    
    op.add_column('candidates', sa.Column('user_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_candidates_user', 'candidates', 'users', ['user_id'], ['id'], ondelete='SET NULL')

    # 13. Seed default roles and permissions
    # Seeding Roles
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.UUID()),
        sa.column('name', sa.String()),
        sa.column('description', sa.String())
    )
    op.bulk_insert(
        roles_table,
        [
            {"id": "d003b5b5-7788-4db8-b5b5-77884db8b5b5", "name": "ADMINISTRATOR", "description": "System administrator with full control."},
            {"id": "e114c6c6-8899-5ec9-c6c6-88995ec9c6c6", "name": "RECRUITER", "description": "Recruiter responsible for managing jobs and candidate applications."},
            {"id": "f225d7d7-99aa-6fd0-d7d7-99aa6fd0d7d7", "name": "CANDIDATE", "description": "Candidate applicant participating in interview processes."},
            {"id": "a336e8e8-00bb-7fe1-e8e8-00bb7fe1e8e8", "name": "HIRING_MANAGER", "description": "Hiring manager evaluating candidates and scoring transcripts."}
        ]
    )

    # Seeding Permissions
    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.UUID()),
        sa.column('name', sa.String()),
        sa.column('description', sa.String())
    )
    op.bulk_insert(
        permissions_table,
        [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "users:view", "description": "Ability to view general user details."},
            {"id": "00000000-0000-0000-0000-000000000002", "name": "users:manage", "description": "Ability to activate/suspend user accounts."},
            {"id": "00000000-0000-0000-0000-000000000003", "name": "roles:assign", "description": "Ability to assign/remove user roles."},
            {"id": "00000000-0000-0000-0000-000000000004", "name": "audit:view", "description": "Ability to view system audit logs."},
            {"id": "00000000-0000-0000-0000-000000000005", "name": "reports:view", "description": "Ability to view final interview scoring reports."}
        ]
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_constraint('fk_candidates_user', 'candidates', type_='foreignkey')
    op.drop_column('candidates', 'user_id')

    op.drop_constraint('fk_recruiters_user', 'recruiters', type_='foreignkey')
    op.drop_column('recruiters', 'user_id')

    op.drop_table('audit_logs')
    op.drop_table('login_history')
    op.drop_table('user_sessions')
    op.drop_table('email_verification_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
