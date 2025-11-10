"""add last_read_at to conversation_participants

Revision ID: 0001_add_last_read_at
Revises:
Create Date: 2025-11-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_last_read_at'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('conversation_participants', sa.Column('last_read_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('conversation_participants', 'last_read_at')
