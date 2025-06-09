"""Add reported_dreams table

Revision ID: 2024_03_21_000001
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '2024_03_21_000001'
down_revision = '2023_10_01_000002'

def upgrade():
    op.create_table(
        'reported_dreams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dream_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=200), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dream_id'], ['dream_entries.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reported_dreams_id'), 'reported_dreams', ['id'], unique=False)
    op.create_index(op.f('ix_reported_dreams_timestamp'), 'reported_dreams', ['timestamp'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_reported_dreams_timestamp'), table_name='reported_dreams')
    op.drop_index(op.f('ix_reported_dreams_id'), table_name='reported_dreams')
    op.drop_table('reported_dreams') 