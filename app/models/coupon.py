from app import db
from datetime import datetime

class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_amount = db.Column(db.Float, nullable=False)      # e.g., 10 for 10% or $10
    minimum_order = db.Column(db.Float, default=0)             # minimum subtotal to apply
    max_uses = db.Column(db.Integer, default=1)                # total uses allowed (0 = unlimited)
    used_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_valid(self, subtotal):
        """Check if coupon is valid for given subtotal"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if subtotal < self.minimum_order:
            return False
        return True

    def apply_discount(self, subtotal):
        """Calculate discount amount for given subtotal"""
        if self.discount_type == 'percentage':
            return subtotal * (self.discount_amount / 100)
        else:  # fixed
            return min(self.discount_amount, subtotal)  # can't exceed subtotal

    def __repr__(self):
        return f'<Coupon {self.code}>'