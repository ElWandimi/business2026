# app/routes/wishlist.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.wishlist import Wishlist, WishlistItem
from app.models.product import Product, Variant
from app.models.cart import Cart, CartItem
from datetime import datetime

bp = Blueprint('wishlist', __name__)

@bp.route('/')
@login_required
def view_wishlist():
    """Display user's wishlist."""
    # Ensure user has a wishlist
    if not current_user.wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.commit()
    else:
        wishlist = current_user.wishlist
    return render_template('wishlist.html', wishlist=wishlist)

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add a product to wishlist."""
    product = Product.query.get_or_404(product_id)
    
    # Get or create wishlist
    if not current_user.wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.flush()
    else:
        wishlist = current_user.wishlist
    
    # Check if already in wishlist
    existing = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product.id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Product already in wishlist'})
    
    item = WishlistItem(wishlist_id=wishlist.id, product_id=product.id)
    db.session.add(item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Added to wishlist'})

@bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    """Remove an item from wishlist."""
    item = WishlistItem.query.get_or_404(item_id)
    
    # Ensure item belongs to current user
    if item.wishlist.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('wishlist.view_wishlist'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from wishlist.', 'success')
    return redirect(url_for('wishlist.view_wishlist'))

@bp.route('/move-to-cart/<int:item_id>', methods=['POST'])
@login_required
def move_to_cart(item_id):
    """Move wishlist item to cart – adds the first active variant to cart."""
    item = WishlistItem.query.get_or_404(item_id)
    
    # Ensure item belongs to current user
    if item.wishlist.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('wishlist.view_wishlist'))
    
    product = item.product
    
    # Find the first active variant of this product
    variant = Variant.query.filter_by(product_id=product.id, is_active=True).first()
    if not variant:
        flash('This product has no active variants and cannot be added to cart.', 'danger')
        return redirect(url_for('wishlist.view_wishlist'))
    
    # Check stock
    if variant.stock <= 0:
        flash('This variant is out of stock.', 'danger')
        return redirect(url_for('wishlist.view_wishlist'))
    
    # Get or create cart for current user
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.flush()
    
    # Check if variant already in cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, variant_id=variant.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=1)
        db.session.add(cart_item)
    
    # Remove wishlist item
    db.session.delete(item)
    db.session.commit()
    
    flash('Item moved to cart.', 'success')
    return redirect(url_for('cart.view_cart'))

@bp.route('/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    """Toggle wishlist status for AJAX."""
    product = Product.query.get_or_404(product_id)
    
    if not current_user.wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.flush()
    else:
        wishlist = current_user.wishlist
    
    existing = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'in_wishlist': False, 'message': 'Removed from wishlist'})
    else:
        item = WishlistItem(wishlist_id=wishlist.id, product_id=product.id)
        db.session.add(item)
        db.session.commit()
        return jsonify({'in_wishlist': True, 'message': 'Added to wishlist'})

@bp.route('/check/<int:product_id>')
@login_required
def check_wishlist(product_id):
    """Check if product is in wishlist (AJAX)."""
    if not current_user.wishlist:
        return jsonify({'in_wishlist': False})
    exists = WishlistItem.query.filter_by(wishlist_id=current_user.wishlist.id, product_id=product_id).first() is not None
    return jsonify({'in_wishlist': exists})