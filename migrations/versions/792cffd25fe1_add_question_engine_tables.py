"""Add Question Engine tables

Revision ID: 792cffd25fe1
Revises: 26b2c7f80629
Create Date: 2026-07-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '792cffd25fe1'
down_revision: Union[str, Sequence[str], None] = '26b2c7f80629'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    # 1. Create question_rubrics table linked to existing questions(id)
    op.create_table(
        'question_rubrics',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('criteria', sa.String(length=255), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rubric_question', 'question_rubrics', ['question_id'], unique=False)

    # 2. Create question_versions table
    op.create_table(
        'question_versions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('statement_snapshot', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_version_question', 'question_versions', ['question_id'], unique=False)

    # 3. Create question_retrieval_logs table
    op.create_table(
        'question_retrieval_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('retrieval_strategy', sa.String(length=100), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_retrieval_log_session', 'question_retrieval_logs', ['interview_session_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('question_retrieval_logs')
    op.drop_table('question_versions')
    op.drop_table('question_rubrics')
