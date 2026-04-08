from app import db
from datetime import datetime

class SupportConversation(db.Model):
    __tablename__ = 'support_conversations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    order_number = db.Column(db.String(50))
    subject = db.Column(db.String(200))
    status = db.Column(db.String(20), default='open')  # open, pending, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add this line:
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationship:
    user = db.relationship('User', backref='support_conversations')

    # You may already have a rating relationship, keep it.
    rating = db.relationship('SupportRating', uselist=False, back_populates='conversation')

    # ... any other fields or methods

class SupportMessage(db.Model):
    __tablename__ = 'support_messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('support_conversations.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'support'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversation = db.relationship('SupportConversation', backref='messages')

class SupportRating(db.Model):
    __tablename__ = 'support_ratings'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('support_conversations.id'), unique=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversation = db.relationship('SupportConversation', back_populates='rating')