from app import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(100))
    comment = db.Column(db.Text)
    verified_purchase = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)  # For admin moderation
    helpful_count = db.Column(db.Integer, default=0)   # For helpful votes (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - using back_populates to avoid duplicate backref conflicts
    user = db.relationship('User', back_populates='reviews')
    product = db.relationship('Product', back_populates='reviews')
    helpful_votes = db.relationship('ReviewHelpful', backref='review', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Review {self.id} - {self.rating} stars>'


class ReviewHelpful(db.Model):
    __tablename__ = 'review_helpful'
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('review_id', 'user_id', name='unique_review_user'),)

    def __repr__(self):
        return f'<ReviewHelpful review={self.review_id} user={self.user_id}>'