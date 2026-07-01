"""Initial migration

Revision ID: 3b26f0f5deda
Revises: 
Create Date: 2026-07-01 12:12:25.271988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3b26f0f5deda'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # 1. Recruiters table
    op.create_table(
        'recruiters',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 2. Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('recruiter_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('experience_level', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_recruiter', 'jobs', ['recruiter_id'], unique=False)

    # 3. Candidates table
    op.create_table(
        'candidates',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('resume_url', sa.Text(), nullable=False),
        sa.Column('parsed_skills', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_candidates_email', 'candidates', ['email'], unique=False)

    # 4. Applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('candidate_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='APPLIED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('candidate_id', 'job_id', name='unique_candidate_job')
    )
    op.create_index('idx_applications_job', 'applications', ['job_id'], unique=False)

    # 5. Active Sessions table
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('session_token', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )
    op.create_index('idx_sessions_token', 'interview_sessions', ['session_token'], unique=False)

    # 6. Questions Bank
    op.create_table(
        'questions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Attempts per Question
    op.create_table(
        'question_attempts',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('response_transcript', sa.Text(), nullable=True),
        sa.Column('auto_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_attempts_session', 'question_attempts', ['session_id'], unique=False)

    # 8. Code Submissions inside attempts
    op.create_table(
        'code_submissions',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('question_attempt_id', sa.UUID(), nullable=False),
        sa.Column('source_code', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('test_cases_passed', sa.Integer(), nullable=False),
        sa.Column('total_test_cases', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('memory_used_bytes', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['question_attempt_id'], ['question_attempts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_submissions_attempt', 'code_submissions', ['question_attempt_id'], unique=False)

    # 9. Proctoring log checks
    op.create_table(
        'proctoring_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('anomaly_type', sa.String(length=100), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_proctor_session', 'proctoring_logs', ['session_id'], unique=False)

    # 10. Final Evaluation Reports
    op.create_table(
        'evaluation_reports',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('overall_score', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('technical_skills_matrix', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('behavioral_skills_matrix', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('summary_verdict', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('evaluation_reports')
    op.drop_index('idx_proctor_session', table_name='proctoring_logs')
    op.drop_table('proctoring_logs')
    op.drop_index('idx_submissions_attempt', table_name='code_submissions')
    op.drop_table('code_submissions')
    op.drop_index('idx_attempts_session', table_name='question_attempts')
    op.drop_table('question_attempts')
    op.drop_table('questions')
    op.drop_index('idx_sessions_token', table_name='interview_sessions')
    op.drop_table('interview_sessions')
    op.drop_index('idx_applications_job', table_name='applications')
    op.drop_table('applications')
    op.drop_index('idx_candidates_email', table_name='candidates')
    op.drop_table('candidates')
    op.drop_index('idx_jobs_recruiter', table_name='jobs')
    op.drop_table('jobs')
    op.drop_table('recruiters')
