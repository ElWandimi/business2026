#!/usr/bin/env python3
"""
Diagnostic script to check image paths and serving.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app
from app.models.product import Product

def debug_images():
    """Debug image paths and serving"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("🔍 IMAGE DEBUGGING")
        print("=" * 60)
        
        # Check upload directories
        upload_base = app.config['UPLOAD_FOLDER']
        products_dir = os.path.join(upload_base, 'products')
        
        print(f"\n📁 Upload base directory: {upload_base}")
        print(f"  Exists: {os.path.exists(upload_base)}")
        print(f"  Absolute path: {os.path.abspath(upload_base)}")
        
        print(f"\n📁 Products directory: {products_dir}")
        print(f"  Exists: {os.path.exists(products_dir)}")
        print(f"  Absolute path: {os.path.abspath(products_dir)}")
        
        if os.path.exists(products_dir):
            files = os.listdir(products_dir)
            print(f"\n📸 Files in products directory ({len(files)}):")
            for f in files:
                file_path = os.path.join(products_dir, f)
                size = os.path.getsize(file_path)
                print(f"  - {f} ({size} bytes)")
        
        # Check static directory for placeholder
        static_dir = os.path.join(app.root_path, 'static', 'images')
        print(f"\n📁 Static images directory: {static_dir}")
        print(f"  Exists: {os.path.exists(static_dir)}")
        
        if os.path.exists(static_dir):
            files = os.listdir(static_dir)
            print(f"  Files: {files}")
        
        # Check products and their image URLs
        products = Product.query.all()
        print(f"\n📦 Products ({len(products)}):")
        for product in products:
            print(f"\n  Product: {product.name} (ID: {product.id})")
            print(f"  Primary image URL: {product.primary_image}")
            
            if product.images:
                for img in product.images:
                    filename = img.image_url.split('/')[-1]
                    file_path = os.path.join(products_dir, filename)
                    exists = os.path.exists(file_path)
                    status = "✅" if exists else "❌"
                    print(f"    {status} {img.image_url}")
                    print(f"        File: {file_path}")
        
        # Test URLs
        print("\n" + "=" * 60)
        print("Test these URLs in your browser:")
        print("=" * 60)
        
        if os.path.exists(products_dir) and files:
            test_file = files[0]
            print(f"Test image: http://localhost:5001/uploads/products/{test_file}")
            print(f"Test image (alt): http://localhost:5001/uploads/{test_file}")
        
        print(f"Placeholder: http://localhost:5001/static/images/no-image.svg")

if __name__ == "__main__":
    debug_images()