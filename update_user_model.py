#!/usr/bin/env python3
"""
Script to update User model to match existing database schema.
Run this to create the User class with the correct fields.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.user import User

def check_user_schema():
    """Check what columns exist in the users table"""
    app = create_app()
    with app.app_context():
        # Reflect the database
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        columns = inspector.get_columns('users')
        
        print("📊 Existing columns in users table:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Check if our model matches
        from app.models.user import User
        model_columns = [c.key for c in User.__table__.columns]
        
        print("\n📋 Columns in your model:")
        for col in model_columns:
            print(f"  - {col}")
        
        # Find missing columns
        missing_in_db = [c for c in model_columns if c not in [col['name'] for col in columns]]
        missing_in_model = [col['name'] for col in columns if col['name'] not in model_columns]
        
        if missing_in_db:
            print(f"\n❌ Columns in model but not in DB: {missing_in_db}")
        if missing_in_model:
            print(f"\n❌ Columns in DB but not in model: {missing_in_model}")
        
        if not missing_in_db and not missing_in_model:
            print("\n✅ Model matches database schema!")

if __name__ == "__main__":
    check_user_schema()