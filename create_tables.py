#!/usr/bin/env python3
"""
Script to create all database tables.
"""
import sys
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.user import User
from app.models.product import Product, Category, ProductImage, Review
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.wishlist import Wishlist, WishlistItem

def create_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🗄️  CREATING DATABASE TABLES")
        print("=" * 60)
        
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")
        
        # Create all tables
        db.create_all()
        print("✅ All tables created successfully!")
        
        # List tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n📊 Tables created: {', '.join(tables)}")
        
        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@business2026.com',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()
            
            # Create cart for admin
            cart = Cart(user_id=admin.id)
            db.session.add(cart)
            
            # Create wishlist for admin
            wishlist = Wishlist(user_id=admin.id)
            db.session.add(wishlist)
            
            db.session.commit()
            print("\n👤 Admin user created: admin / admin123")
        else:
            print("\n👤 Admin user already exists")
        
        print("\n" + "=" * 60)
        print("✅ Database setup complete!")
        print("=" * 60)

if __name__ == "__main__":
    create_tables()