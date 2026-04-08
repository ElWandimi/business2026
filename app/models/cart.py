from app import db
from datetime import datetime
from .product import Variant  # Import Variant to establish relationship

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, unique=True)
    session_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', lazy=True, cascade='all, delete-orphan')
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self):
        return sum(item.total for item in self.items)
    
    @property
    def tax(self):
        return self.subtotal * 0.1  # 10% tax – adjust as needed
    
    @property
    def total(self):
        return self.subtotal + self.tax
    
    def __repr__(self):
        return f'<Cart User: {self.user_id} Items: {self.item_count}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cart = db.relationship('Cart', back_populates='items')
    variant = db.relationship('Variant', backref='cart_items')  # establishes reverse relationship
    
    @property
    def total(self):
        """Calculate total price for this cart item based on variant price."""
        # variant.product gives the parent product
        product = self.variant.product
        price = product.base_price + self.variant.price_adjustment
        return price * self.quantity
    
    def __repr__(self):
        return f'<CartItem Variant: {self.variant_id} x{self.quantity}>'