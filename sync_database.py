#!/usr/bin/env python3
"""
Script to sync database schema with models.
Run this to update your database schema.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.order import Order
from app.models.user import User
from app.models.product import Product, Category, ProductImage, Review
from app.models.cart import Cart, CartItem
from app.models.wishlist import Wishlist, WishlistItem
import sqlite3

def sync_database():
    """Sync database schema with models"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🗄️  SYNCING DATABASE SCHEMA")
        print("=" * 60)
        
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")
        
        # Connect directly to SQLite to check schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns in orders table
        cursor.execute("PRAGMA table_info(orders)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"\n📊 Current columns in orders table:")
        for col in column_names:
            print(f"  - {col}")
        
        # Check for columns that might be causing issues
        problem_columns = ['shipping_name', 'shipping_address_line1', 
                          'shipping_address_line2', 'shipping_postal_code', 'carrier']
        
        for col in problem_columns:
            if col in column_names:
                print(f"\n⚠️  Found problematic column: {col}")
                # Option to remove it
                try:
                    # SQLite doesn't support DROP COLUMN directly in older versions
                    # You might need to recreate the table
                    print(f"  To remove this column, you'll need to recreate the table")
                except Exception as e:
                    print(f"  Error: {e}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Schema check complete")
        print("=" * 60)

def recreate_orders_table():
    """WARNING: This will delete all order data!"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("⚠️  RECREATING ORDERS TABLE - ALL DATA WILL BE LOST!")
        print("=" * 60)
        
        confirm = input("Type 'YES' to confirm: ")
        if confirm != "YES":
            print("Cancelled")
            return
        
        # Drop and recreate tables
        db.drop_all()
        db.create_all()
        
        print("✅ Database recreated successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        recreate_orders_table()
    else:
        sync_database()