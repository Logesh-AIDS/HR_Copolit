"""Add Coding Assessment tables

Revision ID: 684b7f7a36e7
Revises: 792cffd25fe1
Create Date: 2026-07-02 10:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '684b7f7a36e7'
down_revision: Union[str, Sequence[str], None] = '792cffd25fe1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create coding_problems table
    op.create_table(
        'coding_problems',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('input_format', sa.Text(), nullable=True),
        sa.Column('output_format', sa.Text(), nullable=True),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('time_limit_ms', sa.Integer(), server_default='2000', nullable=False),
        sa.Column('memory_limit_bytes', sa.Integer(), server_default='268435456', nullable=False),
        sa.Column('reference_solution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create coding_test_cases table
    op.create_table(
        'coding_test_cases',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('problem_id', sa.UUID(), nullable=False),
        sa.Column('input', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('is_hidden', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['coding_problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_test_case_problem', 'coding_test_cases', ['problem_id'], unique=False)

    # 3. Create compilation_logs table
    op.create_table(
        'compilation_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('submission_id', sa.UUID(), nullable=False),
        sa.Column('logs', sa.Text(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['code_submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_compilation_submission', 'compilation_logs', ['submission_id'], unique=False)

    # 4. Create execution_results table
    op.create_table(
        'execution_results',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('submission_id', sa.UUID(), nullable=False),
        sa.Column('test_case_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('actual_output', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('memory_used_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['code_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_case_id'], ['coding_test_cases.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_execution_submission', 'execution_results', ['submission_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('execution_results')
    op.drop_table('compilation_logs')
    op.drop_table('coding_test_cases')
    op.drop_table('coding_problems')
