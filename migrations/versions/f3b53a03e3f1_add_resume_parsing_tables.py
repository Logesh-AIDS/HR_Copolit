"""Add resume parsing tables

Revision ID: f3b53a03e3f1
Revises: a913ebc95935
Create Date: 2026-07-01 13:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3b53a03e3f1'
down_revision: Union[str, Sequence[str], None] = 'a913ebc95935'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create parsed_resumes table
    op.create_table(
        'parsed_resumes',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('github', sa.String(length=255), nullable=True),
        sa.Column('linkedin', sa.String(length=255), nullable=True),
        sa.Column('portfolio', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsing_confidence', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_parsed_resumes_doc', 'parsed_resumes', ['document_id'], unique=False)
    op.create_index('idx_parsed_resumes_user', 'parsed_resumes', ['user_id'], unique=False)

    # 2. Create resume_sections table
    op.create_table(
        'resume_sections',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sections_resume', 'resume_sections', ['parsed_resume_id'], unique=False)

    # 3. Create extracted_skills table
    op.create_table(
        'extracted_skills',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_skills_resume', 'extracted_skills', ['parsed_resume_id'], unique=False)

    # 4. Create experience table
    op.create_table(
        'experience',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_months', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_experience_resume', 'experience', ['parsed_resume_id'], unique=False)

    # 5. Create education table
    op.create_table(
        'education',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('institution', sa.String(length=255), nullable=True),
        sa.Column('degree', sa.String(length=255), nullable=True),
        sa.Column('cgpa', sa.String(length=50), nullable=True),
        sa.Column('graduation_year', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_education_resume', 'education', ['parsed_resume_id'], unique=False)

    # 6. Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('technologies', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_projects_resume', 'projects', ['parsed_resume_id'], unique=False)

    # 7. Create certifications table
    op.create_table(
        'certifications',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('issuing_organization', sa.String(length=255), nullable=True),
        sa.Column('issue_date', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_certs_resume', 'certifications', ['parsed_resume_id'], unique=False)

    # 8. Create languages table
    op.create_table(
        'languages',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('parsed_resume_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('proficiency', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['parsed_resume_id'], ['parsed_resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_languages_resume', 'languages', ['parsed_resume_id'], unique=False)

    # 9. Create parsing_logs table
    op.create_table(
        'parsing_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('log_level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_parsing_logs_doc', 'parsing_logs', ['document_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('parsing_logs')
    op.drop_table('languages')
    op.drop_table('certifications')
    op.drop_table('projects')
    op.drop_table('education')
    op.drop_table('experience')
    op.drop_table('extracted_skills')
    op.drop_table('resume_sections')
    op.drop_table('parsed_resumes')
