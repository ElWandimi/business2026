#!/usr/bin/env python3
"""
Test script to upload a product image.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from app import create_app, db
from app.models.product import Product, ProductImage
import os
import uuid

app = create_app()
with app.app_context():
    # Get the first product
    product = Product.query.first()
    if not product:
        print("❌ No products found. Please add a product first.")
        sys.exit(1)
    
    print(f"📦 Found product: {product.name} (ID: {product.id})")
    
    # Create a test image URL
    test_filename = "4744ceccde814b8caa52c075eb128bdb.jpg"
    test_url = f"/uploads/products/{test_filename}"
    
    # Check if file exists
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
    file_path = os.path.join(upload_dir, test_filename)
    
    if os.path.exists(file_path):
        print(f"✅ Test image exists: {file_path}")
        
        # Add image to product
        image = ProductImage(
            product_id=product.id,
            image_url=test_url,
            is_primary=True,
            sort_order=0
        )
        db.session.add(image)
        db.session.commit()
        
        print(f"✅ Added test image to product: {test_url}")
        print(f"🔍 Check at: http://localhost:5001{test_url}")
    else:
        print(f"❌ Test image not found: {file_path}")
        print("Please ensure you have an image in the uploads/products directory")