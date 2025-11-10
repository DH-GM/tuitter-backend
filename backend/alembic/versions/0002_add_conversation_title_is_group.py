"""add title and is_group to conversations

Revision ID: 0002_add_conversation_title_is_group
Revises: 0001_add_last_read_at
Create Date: 2025-11-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001_add_last_read_at'
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable title and a boolean is_group with safe server default
    op.add_column('conversations', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column(
        'conversations',
        sa.Column('is_group', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade():
    op.drop_column('conversations', 'is_group')
    op.drop_column('conversations', 'title')
