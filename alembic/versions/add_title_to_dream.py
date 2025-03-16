"""add title to dream_entry

Revision ID: {revision_id}
Revises: {previous_revision}
Create Date: {timestamp}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '{revision_id}'
down_revision = '{previous_revision}'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('dream_entry', sa.Column('title', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('dream_entry', 'title')
