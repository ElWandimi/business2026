"""add variants and update cart

Revision ID: db477aa9f6a0
Revises: ddc653ba0b63   # ← now correct
Create Date: 2026-03-05 20:47:04.975134

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = 'db477aa9f6a0'
down_revision = 'ddc653ba0b63'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create variants table
    op.create_table('variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('size', sa.String(length=20), nullable=True),
        sa.Column('color', sa.String(length=30), nullable=True),
        sa.Column('color_code', sa.String(length=7), nullable=True),
        sa.Column('price_adjustment', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('stock', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('image_url', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku')
    )

    # 2. Add base_price column to products (nullable initially)
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('base_price', sa.Float(), nullable=True))

    # 3. Add variant_id column to cart_items (nullable initially)
    with op.batch_alter_table('cart_items') as batch_op:
        batch_op.add_column(sa.Column('variant_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_cart_items_variant_id', 'variants', ['variant_id'], ['id'])

    # 4. Data migration: create default variants for each product
    conn = op.get_bind()

    products = conn.execute(
        sa.text("SELECT id, sku, price, sale_price, stock FROM products")
    ).fetchall()

    variant_mapping = {}
    for product in products:
        if product.sale_price and product.sale_price < product.price:
            base_price = product.sale_price
        else:
            base_price = product.price

        conn.execute(
            sa.text("UPDATE products SET base_price = :base_price WHERE id = :id"),
            {"base_price": base_price, "id": product.id}
        )

        sku = product.sku if product.sku else f"DEFAULT-{product.id}"

        conn.execute(
            sa.text(
                "INSERT INTO variants (product_id, sku, stock, price_adjustment, is_active) "
                "VALUES (:product_id, :sku, :stock, 0, 1)"
            ),
            {"product_id": product.id, "sku": sku, "stock": product.stock}
        )

        result = conn.execute(sa.text("SELECT last_insert_rowid()"))
        variant_id = result.scalar()
        variant_mapping[product.id] = variant_id

    # 5. Update cart_items to point to the new variants
    cart_items = conn.execute(
        sa.text("SELECT id, product_id FROM cart_items")
    ).fetchall()

    for item in cart_items:
        if item.product_id in variant_mapping:
            conn.execute(
                sa.text("UPDATE cart_items SET variant_id = :variant_id WHERE id = :id"),
                {"variant_id": variant_mapping[item.product_id], "id": item.id}
            )

    # 6. Drop product_id column and make variant_id non-nullable
    with op.batch_alter_table('cart_items') as batch_op:
        batch_op.drop_column('product_id')
        batch_op.alter_column('variant_id', nullable=False)

    # 7. Drop old columns from products and make base_price non-nullable
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('price')
        batch_op.drop_column('sale_price')
        batch_op.drop_column('cost_price')
        batch_op.drop_column('stock')
        batch_op.drop_column('low_stock_threshold')
        batch_op.alter_column('base_price', nullable=False)


def downgrade():
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('sale_price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('cost_price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('stock', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('low_stock_threshold', sa.Integer(), nullable=True))
        batch_op.drop_column('base_price')

    conn = op.get_bind()
    variants = conn.execute(
        sa.text("SELECT product_id, stock FROM variants")
    ).fetchall()
    for variant in variants:
        conn.execute(
            sa.text("UPDATE products SET stock = COALESCE(stock, 0) + :stock WHERE id = :product_id"),
            {"stock": variant.stock, "product_id": variant.product_id}
        )

    with op.batch_alter_table('cart_items') as batch_op:
        batch_op.add_column(sa.Column('product_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_cart_items_product_id', 'products', ['product_id'], ['id'])

    cart_items = conn.execute(
        sa.text("SELECT id, variant_id FROM cart_items")
    ).fetchall()
    for item in cart_items:
        variant = conn.execute(
            sa.text("SELECT product_id FROM variants WHERE id = :vid"),
            {"vid": item.variant_id}
        ).fetchone()
        if variant:
            conn.execute(
                sa.text("UPDATE cart_items SET product_id = :pid WHERE id = :id"),
                {"pid": variant.product_id, "id": item.id}
            )

    with op.batch_alter_table('cart_items') as batch_op:
        batch_op.alter_column('product_id', nullable=False)
        batch_op.drop_constraint('fk_cart_items_variant_id', type_='foreignkey')
        batch_op.drop_column('variant_id')

    op.drop_table('variants')