import stripe
from flask import current_app
from app.models.order import Order
from app import db
import uuid
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for handling Stripe payments"""
    
    def __init__(self):
        """Initialize without requiring app context"""
        self.stripe = stripe
        self._stripe_api_key = None
        self._initialized = False
    
    def init_app(self, app):
        """Initialize with app context - call this when app is available"""
        try:
            self._stripe_api_key = app.config.get('STRIPE_SECRET_KEY')
            # Debug print
            print(f"📦 payment_service.init_app: key = {self._stripe_api_key[:8] if self._stripe_api_key else 'None'}")
            if self._stripe_api_key:
                self.stripe.api_key = self._stripe_api_key
                self._initialized = True
                logger.info("✅ Stripe payment service initialized")
            else:
                logger.warning("⚠️ STRIPE_SECRET_KEY not found - payment features will be disabled")
                self._initialized = False
        except Exception as e:
            logger.error(f"❌ Error initializing payment service: {e}")
            self._initialized = False
    
    def is_available(self):
        """Check if payment service is available"""
        return self._initialized and self._stripe_api_key is not None
    
    def get_stripe_api_key(self):
        """Get Stripe API key from current app context (lazy fallback)"""
        if not self._initialized:
            try:
                self._stripe_api_key = current_app.config.get('STRIPE_SECRET_KEY')
                if self._stripe_api_key:
                    self.stripe.api_key = self._stripe_api_key
                    self._initialized = True
                    logger.info("✅ Stripe payment service initialized (lazy)")
            except RuntimeError:
                # Outside app context
                pass
        return self._stripe_api_key
    
    def create_payment_intent(self, amount, currency='usd', metadata=None):
        """Create a Stripe payment intent"""
        if not self.is_available():
            logger.error("Payment service not available - missing Stripe keys")
            return {
                'success': False,
                'error': 'Payment service not configured'
            }
        
        try:
            self.get_stripe_api_key()
            intent = self.stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata=metadata or {}
            )
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Payment intent error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def confirm_payment(self, payment_intent_id):
        """Confirm a payment"""
        if not self.is_available():
            return {'success': False, 'error': 'Payment service not configured'}
        
        try:
            self.get_stripe_api_key()
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
                'payment_intent': intent
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_order_after_payment(self, user_id, cart_items, shipping_info, payment_intent_id, coupon=None):
        """
        Create an order after successful payment.
        - cart_items: list of CartItem objects
        - shipping_info: dict with shipping details
        - payment_intent_id: Stripe payment intent ID
        - coupon: optional Coupon object
        """
        try:
            # Calculate totals
            subtotal = 0.0
            for item in cart_items:
                price = item.variant.product.base_price + item.variant.price_adjustment
                subtotal += price * item.quantity

            tax = subtotal * 0.1  # 10% tax – adjust as needed
            discount_amount = coupon.discount_amount if coupon else 0.0
            total = subtotal + tax - discount_amount

            # Get shipping info
            shipping_first_name = shipping_info.get('shipping_first_name', '')
            shipping_last_name = shipping_info.get('shipping_last_name', '')
            shipping_address = shipping_info.get('shipping_address', '')
            shipping_city = shipping_info.get('shipping_city', '')
            shipping_state = shipping_info.get('shipping_state', '')
            shipping_zip = shipping_info.get('shipping_zip', '')
            shipping_country = shipping_info.get('shipping_country', '')
            shipping_phone = shipping_info.get('shipping_phone', '')

            # Create order
            order = Order(
                order_number=Order().generate_order_number(),
                user_id=user_id,
                status='pending',
                payment_status='paid',
                payment_method='stripe',
                payment_id=payment_intent_id,
                subtotal=subtotal,
                tax=tax,
                total=total,
                discount_amount=discount_amount,
                coupon_code=coupon.code if coupon else None,
                shipping_first_name=shipping_first_name,
                shipping_last_name=shipping_last_name,
                shipping_address=shipping_address,
                shipping_city=shipping_city,
                shipping_state=shipping_state,
                shipping_zip=shipping_zip,
                shipping_country=shipping_country,
                shipping_phone=shipping_phone
            )

            # Save order and items
            db.session.add(order)
            db.session.flush()

            from app.models.order import OrderItem  # Import here to avoid circular imports
            for cart_item in cart_items:
                variant = cart_item.variant
                product = variant.product
                order_item = OrderItem(
                    order_id=order.id,
                    variant_id=variant.id,
                    quantity=cart_item.quantity,
                    price=product.base_price + variant.price_adjustment,
                    variant_sku=variant.sku,
                    variant_size=variant.size,
                    variant_color=variant.color,
                    variant_color_code=variant.color_code,
                    product_name=product.name,
                    product_slug=product.slug,
                    image_url=variant.image_url or product.primary_image
                )
                db.session.add(order_item)
                db.session.delete(cart_item)  # remove from cart

            db.session.commit()
            return {'success': True, 'order': order, 'order_number': order.order_number}

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Order creation error: {e}")
            return {'success': False, 'error': str(e)}

# Create a singleton instance
payment_service = PaymentService()