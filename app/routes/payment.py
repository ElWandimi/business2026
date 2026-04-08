from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash, current_app, session
from flask_login import login_required, current_user
from app.services.payment import payment_service
from app.models.cart import Cart
from app.models.order import Order
from app.models.coupon import Coupon
from app import db
import stripe
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('payment', __name__)

@bp.before_app_request
def initialize_payment_service():
    """Initialize payment service with app context before each request"""
    logger.debug("before_app_request hook triggered")
    payment_service.init_app(current_app)

@bp.route('/checkout')
@login_required
def checkout():
    """Checkout page with Stripe payment"""
    try:
        cart = current_user.cart
        if not cart or cart.item_count == 0:
            flash('Your cart is empty.', 'info')
            return redirect(url_for('cart.view_cart'))

        stripe_public_key = current_app.config.get('STRIPE_PUBLIC_KEY')
        if not stripe_public_key:
            logger.error("Stripe public key missing")
            flash('Payment system not configured.', 'danger')
            return redirect(url_for('cart.view_cart'))

        if not payment_service.is_available():
            logger.error("Payment service not available - missing STRIPE_SECRET_KEY")
            flash('Payment service not configured. Please contact support.', 'danger')
            return redirect(url_for('cart.view_cart'))

        result = payment_service.create_payment_intent(
            amount=cart.total,
            metadata={'user_id': str(current_user.id), 'cart_id': str(cart.id)}
        )

        if not result['success']:
            logger.error(f"Payment intent creation failed: {result.get('error')}")
            flash(f'Payment error: {result.get("error", "Unknown error")}', 'danger')
            return redirect(url_for('cart.view_cart'))

        return render_template('checkout.html',
                               cart=cart,
                               client_secret=result['client_secret'],
                               stripe_public_key=stripe_public_key)

    except Exception as e:
        logger.exception(f"Checkout error: {e}")
        flash('A processing error occurred. Please try again.', 'danger')
        return redirect(url_for('cart.view_cart'))

@bp.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    """Apply a coupon code to the current cart"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        cart = current_user.cart

        if not cart or cart.item_count == 0:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400

        coupon = Coupon.query.filter_by(code=code, is_active=True).first()
        if not coupon:
            return jsonify({'success': False, 'message': 'Invalid coupon code'}), 404

        if not coupon.is_valid(cart.subtotal):
            return jsonify({'success': False, 'message': 'Coupon is not applicable'}), 400

        # Store coupon in session for later use during order creation
        session['applied_coupon'] = coupon.code
        discount = coupon.apply_discount(cart.subtotal)
        # Recalculate totals (assuming tax is still based on subtotal)
        new_total = cart.subtotal + cart.tax - discount

        return jsonify({
            'success': True,
            'message': f'Coupon applied! You saved ${"%.2f" % discount}',
            'discount': discount,
            'new_total': new_total
        })

    except Exception as e:
        logger.exception(f"Apply coupon error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@bp.route('/success', methods=['GET', 'POST'])
@login_required
def payment_success():
    """Handle successful payment"""
    logger.info("=== PAYMENT SUCCESS ENDPOINT CALLED ===")
    try:
        if request.method == 'POST':
            data = request.get_json()
            payment_intent_id = data.get('payment_intent_id')
            shipping_info = data.get('shipping_info')
        else:
            payment_intent_id = request.args.get('payment_intent')
            shipping_info = request.args.get('shipping_info')

        if not payment_intent_id:
            logger.error("No payment intent ID provided")
            if request.method == 'POST':
                return jsonify({'error': 'Missing payment intent ID'}), 400
            else:
                flash('Payment information missing.', 'danger')
                return redirect(url_for('cart.view_cart'))

        cart = current_user.cart
        if not cart or cart.item_count == 0:
            logger.error("Cart is empty")
            if request.method == 'POST':
                return jsonify({'error': 'Cart is empty'}), 400
            else:
                flash('Your cart is empty.', 'info')
                return redirect(url_for('cart.view_cart'))

        # Retrieve coupon from session if any
        coupon_code = session.pop('applied_coupon', None)
        coupon = None
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                # Increment usage count
                coupon.used_count += 1
                db.session.add(coupon)

        if isinstance(shipping_info, str):
            try:
                shipping_info = json.loads(shipping_info)
            except json.JSONDecodeError:
                shipping_info = {}

        result = payment_service.create_order_after_payment(
            user_id=current_user.id,
            cart_items=cart.items,
            shipping_info=shipping_info or {},
            payment_intent_id=payment_intent_id,
            coupon=coupon  # pass coupon to service
        )

        if result['success']:
            logger.info(f"Order created: {result['order_number']}")
            # Send order confirmation email
            try:
                from app.services.email import send_order_confirmation
                send_order_confirmation(result['order'])
            except Exception as e:
                current_app.logger.error(f"Order confirmation email error: {e}")

            if request.method == 'POST':
                return jsonify({
                    'success': True,
                    'order_number': result['order_number'],
                    'redirect_url': url_for('payment.order_confirmation', order_id=result['order'].id)
                })
            else:
                flash('Payment successful! Your order has been placed.', 'success')
                return redirect(url_for('payment.order_confirmation', order_id=result['order'].id))
        else:
            logger.error(f"Order creation failed: {result.get('error')}")
            if request.method == 'POST':
                return jsonify({'error': result.get('error', 'Order creation failed')}), 500
            else:
                flash(f'Order creation error: {result.get("error")}', 'danger')
                return redirect(url_for('cart.view_cart'))

    except Exception as e:
        logger.exception(f"Payment success error: {e}")
        if request.method == 'POST':
            return jsonify({'error': 'Internal server error'}), 500
        else:
            flash('An error occurred while processing your order.', 'danger')
            return redirect(url_for('cart.view_cart'))

@bp.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    return render_template('order_confirmation.html', order=order)

@bp.route('/cancel')
@login_required
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('cart.view_cart'))

@bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    try:
        payment_service.get_stripe_api_key()
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config.get('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'payment_intent.succeeded':
        logger.info(f"Payment succeeded: {event['data']['object']['id']}")
    return jsonify({'status': 'success'})