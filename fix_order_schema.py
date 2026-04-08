#!/usr/bin/env python3
import sqlite3
import os

db_path = os.path.join('instance', 'ecommerce.db')

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get current columns
cursor.execute("PRAGMA table_info(orders)")
columns = cursor.fetchall()
print("Current columns:", [col[1] for col in columns])

# Since SQLite doesn't support dropping columns easily,
# we need to recreate the table

# First, get all data
cursor.execute("SELECT * FROM orders")
orders_data = cursor.fetchall()

# Get column names for reference
column_names = [col[1] for col in columns]

# Create new table with correct schema
cursor.execute("""
CREATE TABLE orders_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_id VARCHAR(200),
    subtotal FLOAT NOT NULL DEFAULT 0,
    tax FLOAT DEFAULT 0,
    shipping_cost FLOAT DEFAULT 0,
    discount FLOAT DEFAULT 0,
    total FLOAT NOT NULL DEFAULT 0,
    shipping_first_name VARCHAR(50),
    shipping_last_name VARCHAR(50),
    shipping_address TEXT,
    shipping_city VARCHAR(50),
    shipping_state VARCHAR(50),
    shipping_zip VARCHAR(20),
    shipping_country VARCHAR(50),
    shipping_phone VARCHAR(20),
    shipping_email VARCHAR(120),
    billing_first_name VARCHAR(50),
    billing_last_name VARCHAR(50),
    billing_address TEXT,
    billing_city VARCHAR(50),
    billing_state VARCHAR(50),
    billing_zip VARCHAR(20),
    billing_country VARCHAR(50),
    notes TEXT,
    tracking_number VARCHAR(100),
    estimated_delivery DATE,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Copy data (mapping old columns to new ones)
for row in orders_data:
    # Create a dict of old data
    old_data = dict(zip(column_names, row))
    
    # Insert into new table with only the columns we want
    cursor.execute("""
    INSERT INTO orders_new (
        id, order_number, user_id, status, payment_status, payment_method,
        payment_id, subtotal, tax, shipping_cost, discount, total,
        shipping_first_name, shipping_last_name, shipping_address,
        shipping_city, shipping_state, shipping_zip, shipping_country,
        shipping_phone, shipping_email,
        billing_first_name, billing_last_name, billing_address,
        billing_city, billing_state, billing_zip, billing_country,
        notes, tracking_number, estimated_delivery, delivered_at,
        created_at, updated_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        old_data.get('id'), old_data.get('order_number'), old_data.get('user_id'),
        old_data.get('status', 'pending'), old_data.get('payment_status', 'pending'),
        old_data.get('payment_method'), old_data.get('payment_id'),
        old_data.get('subtotal', 0), old_data.get('tax', 0),
        old_data.get('shipping_cost', 0), old_data.get('discount', 0),
        old_data.get('total', 0),
        old_data.get('shipping_first_name'), old_data.get('shipping_last_name'),
        old_data.get('shipping_address'), old_data.get('shipping_city'),
        old_data.get('shipping_state'), old_data.get('shipping_zip'),
        old_data.get('shipping_country'), old_data.get('shipping_phone'),
        old_data.get('shipping_email'),
        old_data.get('billing_first_name'), old_data.get('billing_last_name'),
        old_data.get('billing_address'), old_data.get('billing_city'),
        old_data.get('billing_state'), old_data.get('billing_zip'),
        old_data.get('billing_country'),
        old_data.get('notes'), old_data.get('tracking_number'),
        old_data.get('estimated_delivery'), old_data.get('delivered_at'),
        old_data.get('created_at'), old_data.get('updated_at')
    ))

# Drop old table and rename new one
cursor.execute("DROP TABLE orders")
cursor.execute("ALTER TABLE orders_new RENAME TO orders")

conn.commit()
conn.close()

print("✅ Orders table schema fixed!")