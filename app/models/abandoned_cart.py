# app/models/abandoned_cart.py
from app import db
from datetime import datetime

class AbandonedCart(db.Model):
    __tablename__ = 'abandoned_carts'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    first_sent_at = db.Column(db.DateTime, nullable=True)
    second_sent_at = db.Column(db.DateTime, nullable=True)
    recovered_at = db.Column(db.DateTime, nullable=True)
    coupon_code = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cart = db.relationship('Cart', backref='abandoned_record')
    user = db.relationship('User', backref='abandoned_carts')

    def __repr__(self):
        return f'<AbandonedCart cart:{self.cart_id}>'