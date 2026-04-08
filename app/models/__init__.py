"""
Models package for Business2026 application.
"""
# Import all models
from app.models.user import User
from app.models.product import Product, Category, ProductImage, Variant   # removed Review, ReviewHelpful
from app.models.review import Review, ReviewHelpful                        # added
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.wishlist import Wishlist, WishlistItem
from app.models.address import Address
from app.models.payment_method import PaymentMethod
from app.models.coupon import Coupon
from app.models.support import SupportConversation, SupportMessage, SupportRating
from app.models.settings import Settings
from app.models.notification import Notification
from app.models.abandoned_cart import AbandonedCart
from app.models.promotion import Promotion
from app.models.role import Role, Permission
from app.models.admin_log import AdminLog
from app.models.gift_card import GiftCard

# Define what gets imported with "from app.models import *"
__all__ = [
    # User models
    'User',
    
    # Product models
    'Product',
    'Category',
    'ProductImage',
    'Variant',               # added Variant
    'Review',
    'ReviewHelpful',
    
    # Order models
    'Order',
    'OrderItem',
    
    # Cart models
    'Cart',
    'CartItem',
    
    # Wishlist models
    'Wishlist',
    'WishlistItem',
    
    # Coupon models
    'Coupon',
]

# Optional: Create a function to initialize all models with database
def init_models(db):
    """Initialize any model-specific database configurations."""
    pass

# Optional: Create a function to register model event listeners
def register_model_events(db):
    """Register SQLAlchemy event listeners for models."""
    from sqlalchemy import event
    
    @event.listens_for(Order, 'before_insert')
    def receive_order_before_insert(mapper, connection, target):
        """Generate order number before inserting."""
        if not target.order_number:
            target.order_number = target.generate_order_number()

# Optional: Create a function to get model count statistics
def get_model_stats(db):
    """Get statistics about all models."""
    from sqlalchemy import func
    
    stats = {}
    
    stats['users'] = db.session.query(User).count()
    stats['products'] = db.session.query(Product).count()
    stats['categories'] = db.session.query(Category).count()
    stats['product_images'] = db.session.query(ProductImage).count()
    stats['reviews'] = db.session.query(Review).count()
    stats['orders'] = db.session.query(Order).count()
    stats['order_items'] = db.session.query(OrderItem).count()
    stats['carts'] = db.session.query(Cart).count()
    stats['cart_items'] = db.session.query(CartItem).count()
    stats['wishlists'] = db.session.query(Wishlist).count()
    stats['wishlist_items'] = db.session.query(WishlistItem).count()
    stats['coupons'] = db.session.query(Coupon).count()
    
    if stats['orders'] > 0:
        stats['total_revenue'] = db.session.query(func.sum(Order.total)).scalar() or 0
    
    return stats

# Version information
__version__ = '1.0.0'
__author__ = 'Business2026'