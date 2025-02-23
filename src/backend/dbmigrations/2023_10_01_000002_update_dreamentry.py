from sqlalchemy import Column, String, ForeignKey
from alembic import op

def upgrade():
    # Add email and video_url fields, and update user_id as foreign key
    with op.batch_alter_table('dream_entries') as batch_op:
        batch_op.add_column(Column('email', String(100), nullable=False))
        batch_op.add_column(Column('video_url', String(200)))
        batch_op.add_column(Column('user_id', String(50), ForeignKey('users.id'), nullable=False))
        batch_op.drop_column('user_id')  # Remove the old user_id field

def downgrade():
    with op.batch_alter_table('dream_entries') as batch_op:
        batch_op.drop_column('email')
        batch_op.drop_column('video_url')
        batch_op.drop_column('user_id')  # Drop the new user_id field
        batch_op.add_column(Column('user_id', String(50), nullable=False))  # Restore the old user_id field
