# app/routes/checkout.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import current_user
from app import db
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.product import Variant
from app.models.coupon import Coupon
from app.models.notification import Notification
from app.models.abandoned_cart import AbandonedCart
from app.models.gift_card import GiftCard  # <-- NEW
from app.services.payment import process_payment
from app.services.email import send_order_confirmation
from datetime import datetime
import uuid

bp = Blueprint('checkout', __name__)

def get_cart():
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            return cart
        else:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
            return cart
    else:
        cart_id = session.get('cart_id')
        if cart_id:
            cart = Cart.query.get(cart_id)
            if cart:
                return cart
        session_id = str(uuid.uuid4())
        cart = Cart(session_id=session_id)
        db.session.add(cart)
        db.session.commit()
        session['cart_id'] = cart.id
        return cart

@bp.route('/')
def index():
    cart = get_cart()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    subtotal = 0
    for item in cart_items:
        price = item.variant.product.base_price + item.variant.price_adjustment
        subtotal += price * item.quantity
    tax = subtotal * 0.1
    total = subtotal + tax
    
    return render_template('checkout/index.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         tax=tax,
                         total=total)

@bp.route('/process', methods=['POST'])
def process():
    cart = get_cart()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    # Get form data
    shipping_first_name = request.form.get('shipping_first_name')
    shipping_last_name = request.form.get('shipping_last_name')
    shipping_address = request.form.get('shipping_address')
    shipping_city = request.form.get('shipping_city')
    shipping_state = request.form.get('shipping_state')
    shipping_zip = request.form.get('shipping_zip')
    shipping_country = request.form.get('shipping_country')
    shipping_phone = request.form.get('shipping_phone')
    
    if not all([shipping_first_name, shipping_last_name, shipping_address, shipping_city, shipping_zip]):
        flash('Please fill in all required shipping fields.', 'danger')
        return redirect(url_for('checkout.index'))
    
    # Calculate totals
    subtotal = 0
    for item in cart_items:
        price = item.variant.product.base_price + item.variant.price_adjustment
        subtotal += price * item.quantity
    tax = subtotal * 0.1
    total = subtotal + tax

    # ===== GIFT CARD HANDLING =====
    gift_card_id = session.pop('applied_gift_card', None)
    gift_card = None
    gift_card_used = 0
    gift_card_code = None
    if gift_card_id:
        gift_card = GiftCard.query.get(gift_card_id)
        if gift_card and gift_card.is_active and gift_card.current_balance > 0:
            gift_card_used = min(gift_card.current_balance, total)
            total -= gift_card_used
            gift_card.current_balance -= gift_card_used
            gift_card_code = gift_card.code
            db.session.add(gift_card)

    # Create order
    order = Order(
        order_number=Order().generate_order_number(),
        user_id=current_user.id if current_user.is_authenticated else None,
        session_id=session.get('session_id') if not current_user.is_authenticated else None,
        status='pending',
        payment_status='pending',
        subtotal=subtotal,
        tax=tax,
        total=total,
        shipping_first_name=shipping_first_name,
        shipping_last_name=shipping_last_name,
        shipping_address=shipping_address,
        shipping_city=shipping_city,
        shipping_state=shipping_state,
        shipping_zip=shipping_zip,
        shipping_country=shipping_country,
        shipping_phone=shipping_phone,
        gift_card_used=gift_card_used,
        gift_card_code=gift_card_code
    )
    db.session.add(order)
    db.session.flush()
    
    # Create order items and deduct stock
    for cart_item in cart_items:
        variant = cart_item.variant
        product = variant.product
        
        if variant.stock < cart_item.quantity:
            db.session.rollback()
            flash(f'Sorry, {product.name} is out of stock.', 'danger')
            return redirect(url_for('cart.view_cart'))
        
        variant.stock -= cart_item.quantity
        price = product.base_price + variant.price_adjustment
        
        order_item = OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            quantity=cart_item.quantity,
            price=price,
            variant_sku=variant.sku,
            variant_size=variant.size,
            variant_color=variant.color,
            variant_color_code=variant.color_code,
            product_name=product.name,
            product_slug=product.slug,
            image_url=variant.image_url or product.primary_image
        )
        db.session.add(order_item)
        db.session.delete(cart_item)
    
    # Clear cart session if guest
    if not current_user.is_authenticated:
        session.pop('cart_id', None)
    
    db.session.commit()
    
    # ===== NOTIFICATION: New order =====
    try:
        notif = Notification(
            type='new_order',
            title=f'New Order #{order.order_number}',
            message=f'Order total: ${order.total:.2f}',
            link=url_for('admin.order_detail', order_id=order.id)
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to create order notification: {e}")
    
    # ===== MARK ABANDONED CART AS RECOVERED =====
    try:
        abandoned = AbandonedCart.query.filter_by(cart_id=cart.id).first()
        if abandoned:
            abandoned.recovered_at = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to mark abandoned cart as recovered: {e}")
    
    # Send confirmation email
    try:
        send_order_confirmation(order)
    except Exception as e:
        current_app.logger.error(f"Failed to send order confirmation: {e}")

        # ===== NOTIFICATION: Order confirmation =====
    if order.user_id:
        try:
            notif = Notification(
                user_id=order.user_id,
                type='order_confirmation',
                title=f'Order #{order.order_number} confirmed',
                message=f'Your order total: ${order.total:.2f}',
                link=url_for('auth.order_detail', order_id=order.id)
            )
            db.session.add(notif)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to create order confirmation notification: {e}")
    
    flash('Order placed successfully!', 'success')
    return redirect(url_for('checkout.confirmation', order_id=order.id))

@bp.route('/confirmation/<int:order_id>')
def confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    # Security check
    if current_user.is_authenticated:
        if order.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
    else:
        if order.session_id != session.get('session_id'):
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
    return render_template('checkout/confirmation.html', order=order)

# ===== GIFT CARD APPLY ENDPOINT =====
@bp.route('/apply-gift-card', methods=['POST'])
def apply_gift_card():
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    cart = get_cart()
    if not cart or cart.item_count == 0:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    gift_card = GiftCard.query.filter_by(code=code, is_active=True).first()
    if not gift_card:
        return jsonify({'success': False, 'message': 'Invalid gift card code'}), 404
    if gift_card.current_balance <= 0:
        return jsonify({'success': False, 'message': 'Gift card has no remaining balance'}), 400
    if gift_card.expires_at and gift_card.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Gift card has expired'}), 400

    # Store applied gift card in session
    session['applied_gift_card'] = gift_card.id

    return jsonify({
        'success': True,
        'message': f'Gift card applied! Balance: ${gift_card.current_balance:.2f}',
        'gift_card_id': gift_card.id
    })