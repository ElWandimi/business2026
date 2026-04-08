from app import db
from datetime import datetime

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='Business2026')
    site_url = db.Column(db.String(200), default='http://localhost:5001')
    admin_email = db.Column(db.String(120), default='admin@business2026.com')
    currency_code = db.Column(db.String(3), default='USD')
    currency_symbol = db.Column(db.String(5), default='$')
    tax_rate = db.Column(db.Float, default=0.0)
    tax_included = db.Column(db.Boolean, default=False)
    order_prefix = db.Column(db.String(10), default='ORD-')
    low_stock_threshold = db.Column(db.Integer, default=5)
    enable_reviews = db.Column(db.Boolean, default=True)
    enable_wishlist = db.Column(db.Boolean, default=True)
    enable_gift_cards = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Return the singleton settings object (create if not exists)."""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings