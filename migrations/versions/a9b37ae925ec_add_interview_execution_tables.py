"""Add interview execution tables

Revision ID: a9b37ae925ec
Revises: 3ff312ba034c
Create Date: 2026-07-02 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a9b37ae925ec'
down_revision: Union[str, Sequence[str], None] = '3ff312ba034c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Alter existing interview_sessions table to add interview_plan_id column
    op.add_column('interview_sessions', sa.Column('interview_plan_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_session_plan',
        'interview_sessions', 'interview_plans',
        ['interview_plan_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('idx_session_plan_link', 'interview_sessions', ['interview_plan_id'], unique=False)

    # 2. Create session_runtime_states table
    op.create_table(
        'session_runtime_states',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('current_round_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_question_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_difficulty', sa.String(length=50), server_default='MEDIUM', nullable=False),
        sa.Column('current_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('remaining_time_seconds', sa.Integer(), server_default='3600', nullable=False),
        sa.Column('connection_status', sa.String(length=50), server_default='DISCONNECTED', nullable=False),
        sa.Column('warnings_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('pause_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reconnect_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('adaptive_decisions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_runtime_session', 'session_runtime_states', ['interview_session_id'], unique=True)

    # 3. Create state_histories table
    op.create_table(
        'state_histories',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('from_state', sa.String(length=50), nullable=False),
        sa.Column('to_state', sa.String(length=50), nullable=False),
        sa.Column('transitioned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_state_hist_session', 'state_histories', ['interview_session_id'], unique=False)

    # 4. Create round_progress table
    op.create_table(
        'round_progress',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('round_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('round_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('score_awarded', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_round_prog_session', 'round_progress', ['interview_session_id'], unique=False)

    # 5. Create question_progress table
    op.create_table(
        'question_progress',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('round_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('question_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_skipped', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_question_prog_session', 'question_progress', ['interview_session_id'], unique=False)

    # 6. Create runtime_events table
    op.create_table(
        'runtime_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_runtime_event_session', 'runtime_events', ['interview_session_id'], unique=False)

    # 7. Create timer_snapshots table
    op.create_table(
        'timer_snapshots',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('timer_name', sa.String(length=100), nullable=False),
        sa.Column('elapsed_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('remaining_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_timer_snap_session', 'timer_snapshots', ['interview_session_id'], unique=False)

    # 8. Create connection_logs table
    op.create_table(
        'connection_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('event', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conn_log_session', 'connection_logs', ['interview_session_id'], unique=False)

    # 9. Create recovery_logs table
    op.create_table(
        'recovery_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('success', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('restored_elapsed_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recovery_log_session', 'recovery_logs', ['interview_session_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('recovery_logs')
    op.drop_table('connection_logs')
    op.drop_table('timer_snapshots')
    op.drop_table('runtime_events')
    op.drop_table('question_progress')
    op.drop_table('round_progress')
    op.drop_table('state_histories')
    op.drop_table('session_runtime_states')
    
    op.drop_constraint('fk_session_plan', 'interview_sessions', type_='foreignkey')
    op.drop_index('idx_session_plan_link', table_name='interview_sessions')
    op.drop_column('interview_sessions', 'interview_plan_id')
