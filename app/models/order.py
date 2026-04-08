# app/models/order.py
from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    payment_id = db.Column(db.String(100))  # NEW: Stripe payment intent ID
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    shipping_cost = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False)
    coupon_code = db.Column(db.String(50))
    discount_amount = db.Column(db.Float, default=0.0)
    
    # Shipping details
    shipping_first_name = db.Column(db.String(100))
    shipping_last_name = db.Column(db.String(100))
    shipping_address = db.Column(db.String(200))
    shipping_city = db.Column(db.String(100))
    shipping_state = db.Column(db.String(100))
    shipping_zip = db.Column(db.String(20))
    shipping_country = db.Column(db.String(100))
    shipping_phone = db.Column(db.String(20))
    
    # Billing details (if different)
    billing_first_name = db.Column(db.String(100))
    billing_last_name = db.Column(db.String(100))
    billing_address = db.Column(db.String(200))
    billing_city = db.Column(db.String(100))
    billing_state = db.Column(db.String(100))
    billing_zip = db.Column(db.String(20))
    billing_country = db.Column(db.String(100))
    
    # Tracking
    tracking_number = db.Column(db.String(100))
    carrier = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', lazy=True, cascade='all, delete-orphan')
    
    def generate_order_number(self):
        import random
        import string
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"ORD-{timestamp}-{random_chars}"
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of order
    
    # Snapshot of variant details
    variant_sku = db.Column(db.String(50))
    variant_size = db.Column(db.String(20))
    variant_color = db.Column(db.String(30))
    variant_color_code = db.Column(db.String(7))
    product_name = db.Column(db.String(200))
    product_slug = db.Column(db.String(200))
    image_url = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', back_populates='items')
    variant = db.relationship('Variant')
    
    @property
    def total(self):
        return self.price * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'