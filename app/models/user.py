"""
User model for Business2026 application.
Handles user authentication, profile management, and relationships.
"""

from app import db, login_manager
from flask_login import UserMixin
from flask import current_app
from datetime import datetime
import hashlib
import hmac
import os

# Association tables for RBAC
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication fields
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    
    # Personal information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    
    # Address fields
    address_line1 = db.Column(db.String(100))
    address_line2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='USA')
    
    # User status
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    
    # Email verification token
    email_verification_token = db.Column(db.String(100))
    
    # Password reset
    reset_password_token = db.Column(db.String(100))
    reset_password_expires = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    
    # Stripe customer ID
    stripe_customer_id = db.Column(db.String(100))

    # Language & currency preferences
    language = db.Column(db.String(10), default='en')
    currency = db.Column(db.String(3), default='USD')

    # Abandoned cart email opt-out
    email_abandoned_cart_opt_out = db.Column(db.Boolean, default=False)   
    
    # ============ RELATIONSHIPS ============
    
    # Order relationship
    orders = db.relationship(
        'Order', 
        back_populates='user', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Cart relationship - One user has one cart
    cart = db.relationship(
        'Cart', 
        back_populates='user', 
        uselist=False,  # One-to-one relationship
        cascade='all, delete-orphan'
    )
    
    # Reviews relationship
    reviews = db.relationship(
        'Review', 
        back_populates='user', 
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='desc(Review.created_at)'
    )
    
    # Wishlist relationship - One user has one wishlist
    wishlist = db.relationship(
        'Wishlist', 
        back_populates='user', 
        uselist=False,  # One-to-one relationship
        cascade='all, delete-orphan'
    )
    
    # Addresses relationship
    addresses = db.relationship(
        'Address',
        back_populates='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # Payment methods relationship
    payment_methods = db.relationship(
        'PaymentMethod',
        back_populates='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # ============ RBAC RELATIONSHIPS ============
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        lazy='subquery',
        backref=db.backref('users', lazy=True)
    )
    permissions = db.relationship(
        'Permission',
        secondary=user_permissions,
        lazy='subquery',
        backref=db.backref('users', lazy=True)
    )
    
    # ============ PASSWORD HASHING ============
    
    # Password hashing method detection
    try:
        import bcrypt
        BCRYPT_AVAILABLE = True
    except ImportError:
        BCRYPT_AVAILABLE = False
        import warnings
        warnings.warn("bcrypt not installed. Using SHA256 for password hashing (less secure).")

    # ============ PROPERTIES ============
    
    @property
    def full_name(self):
        """Return the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    @property
    def initials(self):
        """Return user's initials."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        else:
            return self.username[0].upper()

    @property
    def cart_count(self):
        """Get the number of items in user's cart."""
        if self.cart:
            return self.cart.item_count
        return 0

    @property
    def cart_total(self):
        """Calculate the total value of items in cart."""
        if self.cart:
            return self.cart.total
        return 0.0

    @property
    def order_count(self):
        """Get the number of orders placed by user."""
        return self.orders.count()

    @property
    def total_spent(self):
        """Calculate total amount spent by user."""
        from sqlalchemy import func
        result = db.session.query(
            func.sum(Order.total)
        ).filter(
            Order.user_id == self.id,
            Order.payment_status == 'paid'
        ).scalar()
        return result or 0.0

    @property
    def is_admin_user(self):
        """Check if user is admin."""
        return self.is_admin

    @property
    def is_verified_user(self):
        """Check if user is verified."""
        return self.is_verified

    @property
    def has_completed_orders(self):
        """Check if user has completed orders."""
        return self.orders.filter_by(status='completed').count() > 0

    # ============ WISHLIST PROPERTIES ============
    
    @property
    def wishlist_items(self):
        """Get wishlist items for the user."""
        if self.wishlist:
            return list(self.wishlist.items)
        return []
    
    @property
    def wishlist_count(self):
        """Get count of items in wishlist."""
        if self.wishlist:
            return len(self.wishlist.items)
        return 0
    
    @property
    def wishlist_products(self):
        """Get all products in user's wishlist."""
        if self.wishlist:
            return [item.product for item in self.wishlist.items if item.product]
        return []

    # ============ REVIEW PROPERTIES ============
    
    @property
    def review_count(self):
        """Get the number of reviews written by user."""
        return self.reviews.count()

    @property
    def average_rating_given(self):
        """Get average rating given by user across all reviews."""
        if self.review_count > 0:
            from sqlalchemy import func
            result = db.session.query(
                func.avg(Review.rating)
            ).filter(
                Review.user_id == self.id
            ).scalar()
            return round(result, 1) if result else 0
        return 0

    @property
    def verified_reviews(self):
        """Get reviews marked as verified purchases."""
        return self.reviews.filter_by(is_verified=True).all()
    
    @property
    def approved_reviews(self):
        """Get reviews that are approved."""
        return self.reviews.filter_by(is_approved=True).all()
    
    @property
    def helpful_votes_received(self):
        """Get total helpful votes received on user's reviews."""
        from sqlalchemy import func
        result = db.session.query(
            func.sum(Review.helpful_count)
        ).filter(
            Review.user_id == self.id
        ).scalar()
        return result or 0

    # ============ PASSWORD METHODS ============

    def set_password(self, password):
        """Set password hash using bcrypt if available, fallback to SHA256."""
        if self.BCRYPT_AVAILABLE:
            import bcrypt
            salt = bcrypt.gensalt()
            self.password_hash = bcrypt.hashpw(
                password.encode('utf-8'), 
                salt
            ).decode('utf-8')
        else:
            salt = os.urandom(32).hex()
            hash_obj = hashlib.sha256()
            hash_obj.update((password + salt).encode('utf-8'))
            self.password_hash = f"sha256${salt}${hash_obj.hexdigest()}"

    def check_password(self, password):
        """Verify password against stored hash."""
        if not self.password_hash:
            return False
        
        if self.BCRYPT_AVAILABLE and not self.password_hash.startswith('sha256$'):
            try:
                import bcrypt
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    self.password_hash.encode('utf-8')
                )
            except Exception:
                return False
        else:
            if self.password_hash.startswith('sha256$'):
                parts = self.password_hash.split('$')
                if len(parts) == 3:
                    _, salt, stored_hash = parts
                    hash_obj = hashlib.sha256()
                    hash_obj.update((password + salt).encode('utf-8'))
                    return hmac.compare_digest(hash_obj.hexdigest(), stored_hash)
            return False

    def verify_password(self, password):
        """Alias for check_password for compatibility."""
        return self.check_password(password)

    # ============ FLASK-LOGIN METHODS ============

    def get_id(self):
        return str(self.id)

    def is_authenticated_property(self):
        return True

    def is_active_property(self):
        return self.is_active

    def is_anonymous_property(self):
        return False

    def has_role(self, role):
        if role == 'admin':
            return self.is_admin
        elif role == 'super_admin':
            return self.is_super_admin
        elif role == 'verified':
            return self.is_verified
        elif role == 'active':
            return self.is_active
        return False

    # ============ TOKEN GENERATION METHODS ============

    def generate_email_verification_token(self):
        import secrets
        self.email_verification_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.email_verification_token

    def verify_email(self, token):
        if self.email_verification_token == token:
            self.is_verified = True
            self.email_verified_at = datetime.utcnow()
            self.email_verification_token = None
            db.session.commit()
            return True
        return False

    def generate_reset_password_token(self):
        import secrets
        from datetime import timedelta
        self.reset_password_token = secrets.token_urlsafe(32)
        self.reset_password_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        return self.reset_password_token

    def verify_reset_password_token(self, token):
        from datetime import datetime
        if (self.reset_password_token == token and 
            self.reset_password_expires and 
            self.reset_password_expires > datetime.utcnow()):
            return True
        return False

    # ============ PROFILE METHODS ============

    def update_last_login(self, ip_address=None):
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        db.session.commit()

    def get_address_dict(self):
        return {
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country
        }

    def update_address(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()

    def get_cart_or_create(self):
        if not self.cart:
            from app.models.cart import Cart
            cart = Cart(user_id=self.id)
            db.session.add(cart)
            db.session.commit()
            self.cart = cart
        return self.cart

    def clear_cart(self):
        if self.cart:
            self.cart.clear()
            return True
        return False

    # ============ WISHLIST METHODS ============

    def get_wishlist_or_create(self):
        if not self.wishlist:
            from app.models.wishlist import Wishlist
            wishlist = Wishlist(user_id=self.id)
            db.session.add(wishlist)
            db.session.commit()
            self.wishlist = wishlist
        return self.wishlist

    def add_to_wishlist(self, product_id):
        wishlist = self.get_wishlist_or_create()
        return wishlist.add_item(product_id)

    def remove_from_wishlist(self, product_id):
        if self.wishlist:
            return self.wishlist.remove_item(product_id)
        return False

    def toggle_wishlist(self, product_id):
        wishlist = self.get_wishlist_or_create()
        return wishlist.toggle_item(product_id)

    def is_in_wishlist(self, product_id):
        if self.wishlist:
            return self.wishlist.has_product(product_id)
        return False

    def clear_wishlist(self):
        if self.wishlist:
            self.wishlist.clear()
            return True
        return False

    def get_wishlist_products_details(self):
        if self.wishlist:
            return self.wishlist.get_products_with_details()
        return []

    # ============ ORDER METHODS ============

    def get_recent_orders(self, limit=5):
        return self.orders.order_by(Order.created_at.desc()).limit(limit).all()

    def get_order_statistics(self):
        from sqlalchemy import func
        stats = {
            'total_orders': self.order_count,
            'total_spent': self.total_spent,
            'pending_orders': self.orders.filter_by(status='pending').count(),
            'processing_orders': self.orders.filter_by(status='processing').count(),
            'completed_orders': self.orders.filter_by(status='completed').count(),
            'cancelled_orders': self.orders.filter_by(status='cancelled').count()
        }
        if stats['total_orders'] > 0:
            stats['average_order_value'] = stats['total_spent'] / stats['total_orders']
        else:
            stats['average_order_value'] = 0
        return stats

    # ============ REVIEW METHODS ============

    def get_reviews(self, approved_only=True, limit=None):
        from app.models.review import Review   # <--- changed from product to review
        query = self.reviews
        if approved_only:
            query = query.filter_by(is_approved=True)
        query = query.order_by(Review.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    def has_reviewed_product(self, product_id):
        from app.models.review import Review   # <--- changed from product to review
        return Review.query.filter_by(
            user_id=self.id,
            product_id=product_id
        ).first() is not None

    def get_review_for_product(self, product_id):
        from app.models.review import Review   # <--- changed from product to review
        return Review.query.filter_by(
            user_id=self.id,
            product_id=product_id
        ).first()

    def get_helpful_votes_given(self):
        from app.models.review import ReviewHelpful   # <--- changed from product to review
        return ReviewHelpful.query.filter_by(user_id=self.id).all()

    def get_helpful_votes_count(self):
        from app.models.review import ReviewHelpful   # <--- changed from product to review
        return ReviewHelpful.query.filter_by(user_id=self.id).count()

    # ============ SERIALIZATION ============

    def to_dict(self, include_private=False, include_wishlist=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'initials': self.initials,
            'phone': self.phone,
            'address': self.get_address_dict(),
            'is_admin': self.is_admin,
            'is_super_admin': self.is_super_admin,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'cart_count': self.cart_count,
            'wishlist_count': self.wishlist_count,
            'order_count': self.order_count,
            'total_spent': self.total_spent,
            'review_count': self.review_count,
            'average_rating_given': self.average_rating_given,
            'helpful_votes_received': self.helpful_votes_received,
            'stripe_customer_id': self.stripe_customer_id,
            'language': self.language,
            'currency': self.currency,
        }
        
        if include_wishlist and self.wishlist:
            data['wishlist'] = self.wishlist.to_dict()
        
        if include_private:
            data.update({
                'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
                'last_login_ip': self.last_login_ip,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data

    # ============ STATIC METHODS ============

    @staticmethod
    def create_admin(username, email, password, is_super_admin=False, **kwargs):
        admin = User.query.filter(
            db.or_(User.username == username, User.email == email)
        ).first()
        
        if not admin:
            admin = User(
                username=username,
                email=email,
                is_admin=True,
                is_super_admin=is_super_admin,
                is_verified=True,
                email_verified_at=datetime.utcnow(),
                **kwargs
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user '{username}' created successfully!")
            return admin
        else:
            print(f"ℹ️ Admin user '{username}' already exists.")
            return admin

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def find_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def search(query):
        search_term = f"%{query}%"
        return User.query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            )
        ).all()

    @staticmethod
    def get_active_users():
        return User.query.filter_by(is_active=True).all()

    @staticmethod
    def get_verified_users():
        return User.query.filter_by(is_verified=True).all()

    @staticmethod
    def get_recent_users(limit=10):
        return User.query.order_by(User.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_top_reviewers(limit=10):
        from sqlalchemy import func
        from app.models.review import Review   # <--- changed from product to review
        return db.session.query(
            User,
            func.count(Review.id).label('review_count')
        ).join(
            Review, User.id == Review.user_id
        ).filter(
            Review.is_approved == True
        ).group_by(
            User.id
        ).order_by(
            func.count(Review.id).desc()
        ).limit(limit).all()

    @staticmethod
    def get_users_with_wishlists(limit=None):
        from app.models.wishlist import Wishlist, WishlistItem
        query = db.session.query(User).join(
            Wishlist, User.id == Wishlist.user_id
        ).join(
            WishlistItem, Wishlist.id == WishlistItem.wishlist_id
        ).distinct()
        if limit:
            query = query.limit(limit)
        return query.all()

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'

    def generate_unsubscribe_token(self, expires_sec=31536000):
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.id, salt='unsubscribe-abandoned')