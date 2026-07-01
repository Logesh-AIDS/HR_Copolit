"""Add resume intelligence tables

Revision ID: e8c3438f85c8
Revises: f3b53a03e3f1
Create Date: 2026-07-01 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e8c3438f85c8'
down_revision: Union[str, Sequence[str], None] = 'f3b53a03e3f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create candidate_intelligences table
    op.create_table(
        'candidate_intelligences',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('career_level', sa.String(length=50), nullable=True),
        sa.Column('career_focus', sa.String(length=255), nullable=True),
        sa.Column('preferred_roles', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('resume_completeness', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_candidate_int_res', 'candidate_intelligences', ['parsed_resume_id'], unique=False)
    op.create_index('idx_candidate_int_user', 'candidate_intelligences', ['user_id'], unique=False)

    # 2. Create experience_summaries table
    op.create_table(
        'experience_summaries',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('candidate_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('total_experience_months', sa.Integer(), server_default='0', nullable=False),
        sa.Column('relevant_experience_months', sa.Integer(), server_default='0', nullable=False),
        sa.Column('leadership_experience_months', sa.Integer(), server_default='0', nullable=False),
        sa.Column('internship_experience_months', sa.Integer(), server_default='0', nullable=False),
        sa.Column('project_experience_months', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['candidate_intelligence_id'], ['candidate_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_exp_sum_int', 'experience_summaries', ['candidate_intelligence_id'], unique=False)

    # 3. Create skill_confidence table
    op.create_table(
        'skill_confidence',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('candidate_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('experience_years', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('project_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('recency_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('has_certification', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['candidate_intelligence_id'], ['candidate_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_skill_conf_int', 'skill_confidence', ['candidate_intelligence_id'], unique=False)

    # 4. Create feature_store table
    op.create_table(
        'feature_store',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('candidate_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('skills_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('projects_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('avg_project_complexity', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('years_experience', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('education_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('certification_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('skill_diversity', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('tech_breadth', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('tech_depth', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('leadership_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('cloud_exposure', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deployment_experience', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['candidate_intelligence_id'], ['candidate_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_feat_store_int', 'feature_store', ['candidate_intelligence_id'], unique=False)

    # 5. Create candidate_strengths_weaknesses table
    op.create_table(
        'candidate_strengths_weaknesses',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('candidate_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['candidate_intelligence_id'], ['candidate_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_str_weak_int', 'candidate_strengths_weaknesses', ['candidate_intelligence_id'], unique=False)

    # 6. Create technology_taxonomy table
    op.create_table(
        'technology_taxonomy',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('concept_name', sa.String(length=100), nullable=False),
        sa.Column('parent_concept_name', sa.String(length=100), nullable=True),
        sa.Column('relation_type', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_taxonomy_concept', 'technology_taxonomy', ['concept_name'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('technology_taxonomy')
    op.drop_table('candidate_strengths_weaknesses')
    op.drop_table('feature_store')
    op.drop_table('skill_confidence')
    op.drop_table('experience_summaries')
    op.drop_table('candidate_intelligences')
