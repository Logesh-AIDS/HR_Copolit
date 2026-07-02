"""Add interview orchestrator tables

Revision ID: 3ff312ba034c
Revises: 0a02f752362d
Create Date: 2026-07-02 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3ff312ba034c'
down_revision: Union[str, Sequence[str], None] = '0a02f752362d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create interview_plans table
    op.create_table(
        'interview_plans',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('candidate_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('candidate_level', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('total_duration_minutes', sa.Integer(), server_default='60', nullable=False),
        sa.Column('passing_criteria', sa.Float(), server_default='60.0', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PLANNED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_int_plan_cand', 'interview_plans', ['candidate_id'], unique=False)
    op.create_index('idx_int_plan_job', 'interview_plans', ['job_id'], unique=False)

    # 2. Create interview_blueprints table
    op.create_table(
        'interview_blueprints',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_plan_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('rounds_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('termination_rules', sa.Text(), nullable=True),
        sa.Column('adaptive_rules', sa.Text(), nullable=True),
        sa.Column('retry_rules', sa.Text(), nullable=True),
        sa.Column('break_rules', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['interview_plan_id'], ['interview_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_blueprint_plan', 'interview_blueprints', ['interview_plan_id'], unique=False)

    # 3. Create round_definitions table
    op.create_table(
        'round_definitions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_blueprint_id', sa.UUID(), nullable=False),
        sa.Column('round_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('expected_skills', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('max_time_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('question_count', sa.Integer(), server_default='5', nullable=False),
        sa.Column('evaluation_strategy', sa.Text(), nullable=True),
        sa.Column('success_criteria', sa.Text(), nullable=True),
        sa.Column('failure_criteria', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['interview_blueprint_id'], ['interview_blueprints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_round_def_blueprint', 'round_definitions', ['interview_blueprint_id'], unique=False)

    # 4. Create interview_execution_states table
    op.create_table(
        'interview_execution_states',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_plan_id', sa.UUID(), nullable=False),
        sa.Column('current_round_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_question_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_question_id', sa.UUID(), nullable=True),
        sa.Column('remaining_time_seconds', sa.Integer(), server_default='3600', nullable=False),
        sa.Column('score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('skipped_questions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('candidate_actions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('warnings', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('connection_status', sa.String(length=50), server_default='DISCONNECTED', nullable=False),
        sa.Column('is_paused', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_failed', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['interview_plan_id'], ['interview_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_exec_state_plan', 'interview_execution_states', ['interview_plan_id'], unique=False)

    # 5. Create interview_timelines table
    op.create_table(
        'interview_timelines',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_plan_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_plan_id'], ['interview_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_timeline_plan', 'interview_timelines', ['interview_plan_id'], unique=False)

    # 6. Create decision_histories table
    op.create_table(
        'decision_histories',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_plan_id', sa.UUID(), nullable=False),
        sa.Column('decision_type', sa.String(length=100), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_plan_id'], ['interview_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_decision_plan', 'decision_histories', ['interview_plan_id'], unique=False)

    # 7. Create adaptive_decisions table
    op.create_table(
        'adaptive_decisions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_plan_id', sa.UUID(), nullable=False),
        sa.Column('round_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('trigger_event', sa.Text(), nullable=False),
        sa.Column('adjustment_details', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_plan_id'], ['interview_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_adaptive_dec_plan', 'adaptive_decisions', ['interview_plan_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('adaptive_decisions')
    op.drop_table('decision_histories')
    op.drop_table('interview_timelines')
    op.drop_table('interview_execution_states')
    op.drop_table('round_definitions')
    op.drop_table('interview_blueprints')
    op.drop_table('interview_plans')
