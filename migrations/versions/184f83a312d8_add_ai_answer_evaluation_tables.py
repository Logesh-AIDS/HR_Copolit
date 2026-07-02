"""Add AI Answer Evaluation tables

Revision ID: 184f83a312d8
Revises: 684b7f7a36e7
Create Date: 2026-07-02 10:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '184f83a312d8'
down_revision: Union[str, Sequence[str], None] = '684b7f7a36e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create answer_evaluations table
    op.create_table(
        'answer_evaluations',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('candidate_answer', sa.Text(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_evaluation_session', 'answer_evaluations', ['session_id'], unique=False)

    # 2. Create evaluation_rubrics table
    op.create_table(
        'evaluation_rubrics',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('depth_score', sa.Float(), nullable=True),
        sa.Column('clarity_score', sa.Float(), nullable=True),
        sa.Column('accuracy_feedback', sa.Text(), nullable=True),
        sa.Column('completeness_feedback', sa.Text(), nullable=True),
        sa.Column('depth_feedback', sa.Text(), nullable=True),
        sa.Column('clarity_feedback', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['answer_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create concept_coverages table
    op.create_table(
        'concept_coverages',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('concept_name', sa.String(length=255), nullable=False),
        sa.Column('coverage_status', sa.String(length=50), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['answer_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create reasoning_metrics table
    op.create_table(
        'reasoning_metrics',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('logical_flow_score', sa.Float(), nullable=True),
        sa.Column('decomposition_score', sa.Float(), nullable=True),
        sa.Column('tradeoff_discussion_score', sa.Float(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['answer_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Create similarity_scores table
    op.create_table(
        'similarity_scores',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('cosine_similarity', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['answer_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Create evaluations_feedback table
    op.create_table(
        'evaluations_feedback',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('weaknesses', sa.Text(), nullable=True),
        sa.Column('improvements', sa.Text(), nullable=True),
        sa.Column('learning_topics', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['answer_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Create score_histories table
    op.create_table(
        'score_histories',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('updated_score', sa.Float(), nullable=False),
        sa.Column('changer_role', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['answer_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('score_histories')
    op.drop_table('evaluations_feedback')
    op.drop_table('similarity_scores')
    op.drop_table('reasoning_metrics')
    op.drop_table('concept_coverages')
    op.drop_table('evaluation_rubrics')
    op.drop_table('answer_evaluations')
