from app import db
from datetime import datetime

class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='wishlist')
    items = db.relationship('WishlistItem', back_populates='wishlist', lazy=True, cascade='all, delete-orphan')
    
    @property
    def item_count(self):
        return len(self.items)
    
    def __repr__(self):
        return f'<Wishlist User: {self.user_id} Items: {self.item_count}>'

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    wishlist = db.relationship('Wishlist', back_populates='items')
    product = db.relationship('Product', backref='wishlist_items')
    
    __table_args__ = (db.UniqueConstraint('wishlist_id', 'product_id', name='unique_wishlist_product'),)
    
    def __repr__(self):
        return f'<WishlistItem Product: {self.product_id}>'