# app/models/gift_card.py
from app import db
from datetime import datetime
import random
import string

class GiftCard(db.Model):
    __tablename__ = 'gift_cards'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    initial_balance = db.Column(db.Float, nullable=False)
    current_balance = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # user who purchased, or admin
    recipient_email = db.Column(db.String(120), nullable=True)  # optional email to send to
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)

    # Optional relationship
    purchaser = db.relationship('User', foreign_keys=[created_by])

    def generate_code(self, length=12):
        """Generate a random uppercase alphanumeric code."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    def apply_balance(self, amount):
        """Deduct amount from current balance. Returns amount deducted."""
        if amount > self.current_balance:
            raise ValueError("Insufficient balance")
        self.current_balance -= amount
        db.session.commit()
        return amount

    def __repr__(self):
        return f'<GiftCard {self.code}>'