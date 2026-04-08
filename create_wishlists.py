#!/usr/bin/env python3
"""
Script to create wishlists for existing users who don't have one.
Run this after adding the Wishlist model to your application.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.wishlist import Wishlist

def create_wishlists_for_existing_users():
    """Create wishlists for all users who don't have one."""
    
    print("="*60)
    print("Creating wishlists for existing users...")
    print("="*60)
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} total users")
        
        created_count = 0
        skipped_count = 0
        
        for user in users:
            if not user.wishlist:
                wishlist = Wishlist(user_id=user.id)
                db.session.add(wishlist)
                created_count += 1
                print(f"  ✅ Created wishlist for user: {user.username} (ID: {user.id})")
            else:
                skipped_count += 1
                print(f"  ℹ️ User {user.username} already has a wishlist")
        
        # Commit all changes
        db.session.commit()
        
        print("="*60)
        print(f"Summary:")
        print(f"  ✅ Wishlists created: {created_count}")
        print(f"  ℹ️ Users already with wishlists: {skipped_count}")
        print(f"  📊 Total users processed: {len(users)}")
        print("="*60)
        
        return created_count

if __name__ == "__main__":
    create_wishlists_for_existing_users()