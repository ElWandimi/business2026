#!/usr/bin/env python3
"""
Script to fix product image URLs in the database.
"""
import sys
import os
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.product import Product, ProductImage

def fix_image_urls():
    """Update all product image URLs to the correct format"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("🔧 FIXING PRODUCT IMAGE URLs")
        print("=" * 60)
        
        # Get all products
        products = Product.query.all()
        print(f"\n📦 Found {len(products)} products")
        
        # Check each product's images
        for product in products:
            print(f"\n📦 Product: {product.name} (ID: {product.id})")
            
            if product.images:
                print(f"   📸 Has {len(product.images)} images:")
                for img in product.images:
                    # Fix URL format if needed
                    old_url = img.image_url
                    filename = old_url.split('/')[-1]
                    
                    # Ensure URL starts with /uploads/products/
                    if not old_url.startswith('/uploads/products/'):
                        new_url = f"/uploads/products/{filename}"
                        img.image_url = new_url
                        print(f"     ✅ Fixed: {old_url} -> {new_url}")
                    else:
                        print(f"     ✅ Correct: {old_url}")
                    
                    # Check if file exists
                    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
                    file_path = os.path.join(upload_dir, filename)
                    if os.path.exists(file_path):
                        print(f"     📁 File exists: {file_path}")
                    else:
                        print(f"     ❌ File missing: {file_path}")
            else:
                print("   ❌ No images")
        
        # Commit changes
        db.session.commit()
        print("\n✅ Image URLs fixed successfully!")

def check_upload_directory():
    """Check the upload directory and list all files"""
    app = create_app()
    with app.app_context():
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
        print(f"\n📁 Upload directory: {upload_dir}")
        
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            print(f"   Found {len(files)} files:")
            for f in files:
                file_path = os.path.join(upload_dir, f)
                size = os.path.getsize(file_path)
                print(f"   - {f} ({size} bytes)")
        else:
            print(f"   ❌ Directory does not exist, creating...")
            os.makedirs(upload_dir, exist_ok=True)
            print(f"   ✅ Created: {upload_dir}")

if __name__ == "__main__":
    print("=" * 60)
    print("🖼️  PRODUCT IMAGE FIX UTILITY")
    print("=" * 60)
    
    check_upload_directory()
    fix_image_urls()
    
    print("\n" + "=" * 60)
    print("✅ Script completed!")