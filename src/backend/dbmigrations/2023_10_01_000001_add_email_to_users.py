from sqlalchemy import Column, String
from alembic import op

def upgrade():
    # Add email column to users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(Column('email', String(100), nullable=False, unique=True))

def downgrade():
    # Remove email column from users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('email')
