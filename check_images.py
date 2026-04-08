#!/usr/bin/env python3
"""
Script to check and fix product images.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.product import Product, ProductImage

def check_images():
    """Check all products and their images"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("🔍 CHECKING PRODUCT IMAGES")
        print("=" * 60)
        
        products = Product.query.all()
        print(f"\n📦 Found {len(products)} products")
        
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
        print(f"📁 Upload directory: {upload_dir}")
        
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            print(f"📁 Files in upload directory: {len(files)}")
            for f in files[:5]:  # Show first 5 files
                print(f"   - {f}")
        else:
            print(f"❌ Upload directory does not exist")
            os.makedirs(upload_dir, exist_ok=True)
            print(f"✅ Created upload directory")
        
        for product in products:
            print(f"\n📦 Product: {product.name} (ID: {product.id})")
            print(f"   Primary Image URL: {product.primary_image}")
            
            if product.images:
                print(f"   📸 Has {len(product.images)} images:")
                for img in product.images:
                    filename = img.image_url.split('/')[-1]
                    file_path = os.path.join(upload_dir, filename)
                    exists = os.path.exists(file_path)
                    status = "✅" if exists else "❌"
                    print(f"     {status} {img.image_url}")
                    print(f"        File: {file_path} - Exists: {exists}")
                    
                    # Fix URL if needed
                    if not img.image_url.startswith('/uploads/products/'):
                        new_url = f"/uploads/products/{filename}"
                        print(f"        🔧 Fixing URL: {img.image_url} -> {new_url}")
                        img.image_url = new_url
            else:
                print(f"   ❌ No images")
        
        db.session.commit()
        print("\n✅ Image check complete!")

if __name__ == "__main__":
    check_images()