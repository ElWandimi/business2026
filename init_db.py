#!/usr/bin/env python3
"""
Initialize the database and create tables.
Run this script to set up the database.
"""
import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.user import User
from app.models.product import Product, Category, ProductImage, Review
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem

def init_database():
    """Initialize the database and create all tables"""
    print("=" * 60)
    print("🗄️  DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"\n📁 Database path: {db_path}")
        
        # Check if database exists
        db_file = Path(db_path)
        if db_file.exists():
            print(f"✅ Database file exists: {db_file}")
            print(f"📊 File size: {db_file.stat().st_size} bytes")
        else:
            print(f"❌ Database file does not exist yet")
        
        # Create tables
        print("\n📝 Creating database tables...")
        try:
            db.create_all()
            print("✅ Tables created successfully!")
            
            # List all tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n📊 Tables created: {tables}")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    return True

def check_permissions():
    """Check if we have write permissions in the instance directory"""
    print("\n🔍 CHECKING PERMISSIONS")
    print("-" * 40)
    
    # Check instance directory
    instance_dir = Path(__file__).parent / 'instance'
    print(f"📁 Instance directory: {instance_dir}")
    print(f"  - Exists: {instance_dir.exists()}")
    
    if not instance_dir.exists():
        try:
            instance_dir.mkdir(parents=True)
            print(f"  - Created instance directory")
        except Exception as e:
            print(f"  ❌ Could not create instance directory: {e}")
            return False
    
    # Check write permissions
    can_write = os.access(instance_dir, os.W_OK)
    print(f"  - Writable: {can_write}")
    
    if can_write:
        # Try to create a test file
        test_file = instance_dir / 'test.txt'
        try:
            test_file.write_text('test')
            print(f"  ✅ Successfully wrote test file")
            test_file.unlink()
        except Exception as e:
            print(f"  ❌ Could not write test file: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("📦 BUSINESS2026 DATABASE SETUP")
    print("=" * 60)
    
    # Check permissions first
    if check_permissions():
        # Initialize database
        init_database()
    else:
        print("\n❌ Permission check failed. Please check directory permissions.")
    
    print("\n" + "=" * 60)