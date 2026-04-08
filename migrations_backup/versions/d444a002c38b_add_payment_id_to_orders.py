"""add payment_id to orders

Revision ID: d444a002c38b
Revises: 4174195e49f3
Create Date: 2026-03-11 19:32:15.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd444a002c38b'
down_revision = '4174195e49f3'
branch_labels = None
depends_on = None

def upgrade():
    # Add payment_id column to orders table
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('payment_id', sa.String(100), nullable=True))

def downgrade():
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('payment_id')