"""add_multimodal_intelligence_tables

Revision ID: f96e607b54d3
Revises: 184f83a312d8
Create Date: 2026-07-03 08:47:03.275284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f96e607b54d3'
down_revision: Union[str, Sequence[str], None] = '184f83a312d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'multimodal_models_metadata',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('model_type', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'multimodal_timeline_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.JSON(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'multimodal_feature_store',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('feature_value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('feature_source', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_multimodal_timeline_session', 'multimodal_timeline_events', ['session_id'], unique=False)
    op.create_index('idx_multimodal_feature_session', 'multimodal_feature_store', ['session_id'], unique=False)
    op.create_index('idx_multimodal_feature_name', 'multimodal_feature_store', ['feature_name'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_multimodal_feature_name', table_name='multimodal_feature_store')
    op.drop_index('idx_multimodal_feature_session', table_name='multimodal_feature_store')
    op.drop_index('idx_multimodal_timeline_session', table_name='multimodal_timeline_events')
    
    op.drop_table('multimodal_feature_store')
    op.drop_table('multimodal_timeline_events')
    op.drop_table('multimodal_models_metadata')
