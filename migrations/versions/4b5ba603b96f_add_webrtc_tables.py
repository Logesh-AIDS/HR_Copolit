"""Add WebRTC tables

Revision ID: 4b5ba603b96f
Revises: a9b37ae925ec
Create Date: 2026-07-02 09:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b5ba603b96f'
down_revision: Union[str, Sequence[str], None] = 'a9b37ae925ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create webrtc_rooms table
    op.create_table(
        'webrtc_rooms',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('interview_session_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['interview_session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webrtc_room_session', 'webrtc_rooms', ['interview_session_id'], unique=False)

    # 2. Create webrtc_connections table
    op.create_table(
        'webrtc_connections',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('webrtc_room_id', sa.UUID(), nullable=False),
        sa.Column('peer_id', sa.String(length=100), nullable=False),
        sa.Column('connection_state', sa.String(length=50), server_default='NEW', nullable=False),
        sa.Column('packet_loss', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('latency_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('jitter_ms', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['webrtc_room_id'], ['webrtc_rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webrtc_conn_room', 'webrtc_connections', ['webrtc_room_id'], unique=False)

    # 3. Create webrtc_events table
    op.create_table(
        'webrtc_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('webrtc_room_id', sa.UUID(), nullable=False),
        sa.Column('peer_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['webrtc_room_id'], ['webrtc_rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webrtc_event_room', 'webrtc_events', ['webrtc_room_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('webrtc_events')
    op.drop_table('webrtc_connections')
    op.drop_table('webrtc_rooms')
