# app/routes/cart.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import current_user
from app import db
from app.models.cart import Cart, CartItem
from app.models.product import Variant, Product
from datetime import datetime
import uuid
from flask import session


bp = Blueprint('cart', __name__)

def get_cart():
    if current_user.is_authenticated:
        cart = current_user.cart
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
        return cart
    else:
        session_id = session.get('cart_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['cart_session_id'] = session_id
        cart = Cart.query.filter_by(session_id=session_id).first()
        if not cart:
            cart = Cart(session_id=session_id)
            db.session.add(cart)
            db.session.commit()
        return cart

@bp.route('/')
def view_cart():
    """Display cart contents with variant details."""
    cart = get_cart()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    
    for item in cart_items:
        variant = item.variant
        product = variant.product
        item.product_name = product.name
        item.product_slug = product.slug
        item.size = variant.size
        item.color = variant.color
        item.color_code = variant.color_code
        item.price = product.base_price + variant.price_adjustment
        item.image = variant.image_url or product.primary_image
        item.sku = variant.sku
    
    subtotal = sum(item.price * item.quantity for item in cart_items)
    tax = subtotal * 0.1
    total = subtotal + tax
    
    return render_template('cart.html',
                         cart=cart,
                         cart_items=cart_items,
                         subtotal=subtotal,
                         tax=tax,
                         total=total)

@bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Add a variant to the cart. Accepts variant_id or product_id (chooses first variant)."""
    # Get parameters from form or query string (temporary fallback)
    variant_id = request.form.get('variant_id') or request.args.get('variant_id')
    product_id = request.form.get('product_id') or request.args.get('product_id')
    try:
        quantity = int(request.form.get('quantity', request.args.get('quantity', 1)))
    except ValueError:
        quantity = 1

    # Debug logging
    current_app.logger.info(f"Add to cart - variant_id: {variant_id}, product_id: {product_id}, quantity: {quantity}")

    if variant_id:
        variant = Variant.query.get(variant_id)
        if not variant:
            flash('Variant not found.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
    elif product_id:
        product = Product.query.get(product_id)
        if not product:
            flash('Product not found.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
        variant = Variant.query.filter_by(product_id=product.id, is_active=True).first()
        if not variant:
            flash('This product has no active variants.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
    else:
        flash('Please select a product variant.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    if not variant.is_active:
        flash('This variant is no longer available.', 'danger')
        return redirect(request.referrer)

    if variant.stock < quantity:
        flash(f'Sorry, only {variant.stock} in stock.', 'danger')
        return redirect(request.referrer)

    cart = get_cart()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, variant_id=variant.id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=quantity)
        db.session.add(cart_item)

    db.session.commit()
    flash('Item added to cart successfully!', 'success')
    return redirect(url_for('cart.view_cart'))

# ... rest of the routes (update, remove, clear, api/count) remain unchanged ...

@bp.route('/update', methods=['POST'])
def update_cart():
    """Update quantity of a cart item (AJAX)."""
    item_id = request.form.get('item_id', type=int)
    quantity = request.form.get('quantity', type=int)
    
    if not item_id or not quantity or quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    cart_item = CartItem.query.get_or_404(item_id)
    cart = get_cart()
    
    if cart_item.cart_id != cart.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    variant = cart_item.variant
    if variant.stock < quantity:
        return jsonify({'success': False, 'message': f'Only {variant.stock} in stock'}), 400
    
    cart_item.quantity = quantity
    db.session.commit()
    
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    subtotal = sum((item.variant.product.base_price + item.variant.price_adjustment) * item.quantity for item in cart_items)
    tax = subtotal * 0.1
    total = subtotal + tax
    item_total = (variant.product.base_price + variant.price_adjustment) * quantity
    
    return jsonify({
        'success': True,
        'item_total': f"${item_total:.2f}",
        'subtotal': f"${subtotal:.2f}",
        'tax': f"${tax:.2f}",
        'total': f"${total:.2f}"
    })

@bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    """Remove an item from cart."""
    cart_item = CartItem.query.get_or_404(item_id)
    cart = get_cart()
    
    if cart_item.cart_id != cart.id:
        flash('Invalid cart item.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart.view_cart'))

@bp.route('/clear', methods=['POST'])
def clear_cart():
    """Clear all items from cart."""
    cart = get_cart()
    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()
    flash('Cart cleared.', 'success')
    return redirect(url_for('cart.view_cart'))

@bp.route('/api/count')
def cart_count():
    """Return cart item count as JSON."""
    cart = get_cart()
    count = sum(item.quantity for item in cart.items)
    return jsonify({'count': count})