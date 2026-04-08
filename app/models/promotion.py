# app/models/promotion.py
from app import db
from datetime import datetime

class Promotion(db.Model):
    __tablename__ = 'promotions'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text)  # optional plain text version
    recipient_count = db.Column(db.Integer, default=0)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    segment = db.Column(db.String(50), default='all')  # e.g., 'all', 'verified', 'has_orders'
    
    user = db.relationship('User')