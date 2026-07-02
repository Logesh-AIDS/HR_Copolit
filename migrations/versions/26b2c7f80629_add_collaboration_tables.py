"""Add Collaboration tables

Revision ID: 26b2c7f80629
Revises: 4b5ba603b96f
Create Date: 2026-07-02 09:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26b2c7f80629'
down_revision: Union[str, Sequence[str], None] = '4b5ba603b96f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create collaboration_chats table
    op.create_table(
        'collaboration_chats',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('sender_id', sa.String(length=100), nullable=False),
        sa.Column('recipient_id', sa.String(length=100), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collab_chat_session', 'collaboration_chats', ['interview_session_id'], unique=False)

    # 2. Create collaboration_whiteboards table
    op.create_table(
        'collaboration_whiteboards',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collab_wb_session', 'collaboration_whiteboards', ['interview_session_id'], unique=False)

    # 3. Create collaboration_files table
    op.create_table(
        'collaboration_files',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('uploader_id', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collab_files_session', 'collaboration_files', ['interview_session_id'], unique=False)

    # 4. Create collaboration_notes table
    op.create_table(
        'collaboration_notes',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('author_role', sa.String(length=50), nullable=False),
        sa.Column('notes_content', sa.Text(), nullable=False),
        sa.Column('is_private', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collab_notes_session', 'collaboration_notes', ['interview_session_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('collaboration_notes')
    op.drop_table('collaboration_files')
    op.drop_table('collaboration_whiteboards')
    op.drop_table('collaboration_chats')
