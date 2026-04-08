"""add addresses and payment methods

Revision ID: <new_id>
Revises: d444a002c38b
Create Date: 2026-03-12 20:35:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '<new_id>'  # replace with the actual generated ID
down_revision = 'd444a002c38b'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add stripe_customer_id to users if not exists
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'stripe_customer_id' not in columns:
        with op.batch_alter_table('users') as batch_op:
            batch_op.add_column(sa.Column('stripe_customer_id', sa.String(100), nullable=True))

    # Create addresses table
    if 'addresses' not in inspector.get_table_names():
        op.create_table('addresses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('address_type', sa.String(20), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True),
            sa.Column('first_name', sa.String(100), nullable=True),
            sa.Column('last_name', sa.String(100), nullable=True),
            sa.Column('company', sa.String(100), nullable=True),
            sa.Column('address_line1', sa.String(200), nullable=False),
            sa.Column('address_line2', sa.String(200), nullable=True),
            sa.Column('city', sa.String(100), nullable=False),
            sa.Column('state', sa.String(100), nullable=True),
            sa.Column('postal_code', sa.String(20), nullable=False),
            sa.Column('country', sa.String(100), nullable=False),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create payment_methods table
    if 'payment_methods' not in inspector.get_table_names():
        op.create_table('payment_methods',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('stripe_payment_method_id', sa.String(100), nullable=False),
            sa.Column('stripe_customer_id', sa.String(100), nullable=True),
            sa.Column('card_brand', sa.String(50), nullable=True),
            sa.Column('card_last4', sa.String(4), nullable=True),
            sa.Column('card_exp_month', sa.Integer(), nullable=True),
            sa.Column('card_exp_year', sa.Integer(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('stripe_payment_method_id')
        )

def downgrade():
    op.drop_table('payment_methods')
    op.drop_table('addresses')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('stripe_customer_id')