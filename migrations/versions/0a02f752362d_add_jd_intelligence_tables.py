"""Add jd intelligence tables

Revision ID: 0a02f752362d
Revises: e8c3438f85c8
Create Date: 2026-07-01 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0a02f752362d'
down_revision: Union[str, Sequence[str], None] = 'e8c3438f85c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create job_intelligences table
    op.create_table(
        'job_intelligences',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('experience_years_required', sa.Integer(), server_default='0', nullable=False),
        sa.Column('expected_seniority', sa.String(length=50), nullable=True),
        sa.Column('interview_difficulty', sa.String(length=50), nullable=True),
        sa.Column('education_requirements', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_intel_job', 'job_intelligences', ['job_id'], unique=False)
    op.create_index('idx_job_intel_doc', 'job_intelligences', ['document_id'], unique=False)

    # 2. Create job_required_skills table
    op.create_table(
        'job_required_skills',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['job_intelligence_id'], ['job_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_req_skills_intel', 'job_required_skills', ['job_intelligence_id'], unique=False)

    # 3. Create job_responsibilities table
    op.create_table(
        'job_responsibilities',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['job_intelligence_id'], ['job_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_resp_intel', 'job_responsibilities', ['job_intelligence_id'], unique=False)

    # 4. Create job_feature_store table
    op.create_table(
        'job_feature_store',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('required_skills_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('skill_diversity', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('required_experience', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('cloud_requirement', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('leadership_requirement', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ai_requirement', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('programming_depth', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('technology_breadth', sa.Float(), server_default='0.0', nullable=False),
        sa.ForeignKeyConstraint(['job_intelligence_id'], ['job_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_feat_store_intel', 'job_feature_store', ['job_intelligence_id'], unique=False)

    # 5. Create job_metadata table
    op.create_table(
        'job_metadata',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['job_intelligence_id'], ['job_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_meta_intel', 'job_metadata', ['job_intelligence_id'], unique=False)

    # 6. Create job_audit_logs table
    op.create_table(
        'job_audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_intelligence_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['job_intelligence_id'], ['job_intelligences.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_audit_intel', 'job_audit_logs', ['job_intelligence_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('job_audit_logs')
    op.drop_table('job_metadata')
    op.drop_table('job_feature_store')
    op.drop_table('job_responsibilities')
    op.drop_table('job_required_skills')
    op.drop_table('job_intelligences')
