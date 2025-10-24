"""add keywords column to dream_entries

Revision ID: add_keywords_001
Revises: add_title_to_dream
Create Date: 2025-10-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_keywords_001'
down_revision = None  # Set to None if this is the first real migration
branch_labels = None
depends_on = None


def upgrade():
    # Add keywords column as array of strings
    op.add_column(
        'dream_entries',
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True)
    )

    # Create GIN index for fast array searching
    op.create_index(
        'ix_dream_entries_keywords',
        'dream_entries',
        ['keywords'],
        postgresql_using='gin'
    )


def downgrade():
    op.drop_index('ix_dream_entries_keywords', table_name='dream_entries')
    op.drop_column('dream_entries', 'keywords')
