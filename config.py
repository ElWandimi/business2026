"""
Configuration module for Business2026 application.
Handles all application configuration settings including database, uploads, and environment variables.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

# Load environment variables from .env file (if present)
load_dotenv()

class Config:
    """Base configuration class."""
    
    # ============ BASIC FLASK CONFIG ============
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production-2026'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # ============ APPLICATION SETTINGS ============
    APP_NAME = os.environ.get('APP_NAME', 'Business2026')
    APP_VERSION = '1.0.0'
    
    # ============ PATH CONFIGURATION ============
    basedir = Path(__file__).parent.absolute()
    BASE_DIR = str(basedir)
    
    INSTANCE_DIR = basedir / 'instance'
    UPLOAD_BASE_DIR = basedir / 'uploads'
    LOGS_DIR = basedir / 'logs'
    
    # ============ DATABASE CONFIGURATION ============
    # Default SQLite (development)
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    db_path = INSTANCE_DIR / 'business2026.db'
    DEFAULT_DATABASE_URI = f'sqlite:///{db_path}'
    
    # For production, prefer DATABASE_URL environment variable
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or DEFAULT_DATABASE_URI
    
    # Only show warning in development if DATABASE_URL mismatches
    if os.environ.get('FLASK_ENV') != 'production':
        env_db_uri = os.environ.get('DATABASE_URL')
        if env_db_uri and env_db_uri != DEFAULT_DATABASE_URI:
            print(f"⚠️  WARNING: DATABASE_URL environment variable is set to '{env_db_uri}'")
            print(f"   but app is configured to use '{DEFAULT_DATABASE_URI}'")
            print("   To avoid confusion, unset DATABASE_URL or update it to match.")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # ============ UPLOAD CONFIGURATION ============
    UPLOAD_FOLDER = str(UPLOAD_BASE_DIR)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'zip'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
    
    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
    UPLOAD_PATHS = {
        'products': str(UPLOAD_BASE_DIR / 'products'),
        'categories': str(UPLOAD_BASE_DIR / 'categories'),
        'users': str(UPLOAD_BASE_DIR / 'users'),
        'temp': str(UPLOAD_BASE_DIR / 'temp'),
        'documents': str(UPLOAD_BASE_DIR / 'documents'),
    }
    for path in UPLOAD_PATHS.values():
        os.makedirs(path, exist_ok=True)
    
    # ============ MAIL SETTINGS ============
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@business2026.com')
    
    # ============ STRIPE PAYMENT SETTINGS ============
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # ============ SITE INFORMATION ============
    SITE_NAME = os.environ.get('SITE_NAME') or 'Business2026'
    SITE_URL = os.environ.get('SITE_URL') or 'http://localhost:5001'
    SITE_EMAIL = os.environ.get('SITE_EMAIL') or 'admin@business2026.com'
    
    # ============ PAGINATION ============
    PRODUCTS_PER_PAGE = int(os.environ.get('PRODUCTS_PER_PAGE') or 12)
    ADMIN_PRODUCTS_PER_PAGE = int(os.environ.get('ADMIN_PRODUCTS_PER_PAGE') or 20)
    ADMIN_USERS_PER_PAGE = int(os.environ.get('ADMIN_USERS_PER_PAGE') or 20)
    ADMIN_ORDERS_PER_PAGE = int(os.environ.get('ADMIN_ORDERS_PER_PAGE') or 20)
    
    # ============ SESSION SETTINGS ============
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('PERMANENT_SESSION_LIFETIME_DAYS', 31)))
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # ============ CSRF PROTECTION ============
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or SECRET_KEY
    WTF_CSRF_TIME_LIMIT = 3600
    
    # ============ CACHE SETTINGS ============
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT') or 300)
    CACHE_KEY_PREFIX = 'business2026_'
    
    # ============ SECURITY HEADERS ============
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    }
    
    # ============ RATE LIMITING ============
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100/hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    # ============ LOGGING ============
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = str(LOGS_DIR / 'app.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES') or 10 * 1024 * 1024)  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT') or 5)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # ============ TIMEZONE ============
    TIMEZONE = os.environ.get('TIMEZONE', 'UTC')
    
    # ============ CURRENCY ============
    CURRENCY_CODE = os.environ.get('CURRENCY_CODE', 'USD')
    CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', '$')
    
    # ============ TAX SETTINGS ============
    TAX_RATE = float(os.environ.get('TAX_RATE') or 0)
    TAX_INCLUDED = os.environ.get('TAX_INCLUDED', 'False').lower() == 'true'
    
    # ============ ORDER SETTINGS ============
    ORDER_PREFIX = os.environ.get('ORDER_PREFIX', 'ORD-')
    ORDER_NUMBER_LENGTH = int(os.environ.get('ORDER_NUMBER_LENGTH') or 8)
    ALLOW_BACKORDERS = os.environ.get('ALLOW_BACKORDERS', 'False').lower() == 'true'
    
    # ============ CART SETTINGS ============
    CART_EXPIRY_DAYS = int(os.environ.get('CART_EXPIRY_DAYS') or 30)
    MAX_CART_ITEMS = int(os.environ.get('MAX_CART_ITEMS') or 50)
    
    # ============ USER SETTINGS ============
    USERNAME_MIN_LENGTH = int(os.environ.get('USERNAME_MIN_LENGTH') or 3)
    USERNAME_MAX_LENGTH = int(os.environ.get('USERNAME_MAX_LENGTH') or 50)
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH') or 6)
    EMAIL_VERIFICATION_REQUIRED = os.environ.get('EMAIL_VERIFICATION_REQUIRED', 'True').lower() == 'true'
    
    # ============ ADMIN SETTINGS ============
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@business2026.com')
    
    # ============ FEATURE FLAGS ============
    ENABLE_REVIEWS = os.environ.get('ENABLE_REVIEWS', 'True').lower() == 'true'
    ENABLE_WISHLIST = os.environ.get('ENABLE_WISHLIST', 'True').lower() == 'true'
    ENABLE_GIFT_CARDS = os.environ.get('ENABLE_GIFT_CARDS', 'False').lower() == 'true'

    # ============ BABEL SETTINGS ============
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'
    
    SESSION_COOKIE_SECURE = False
    CACHE_TYPE = 'simple'
    
    def __init__(self):
        print("🔧 Initializing DevelopmentConfig")
        if self.STRIPE_PUBLIC_KEY and self.STRIPE_SECRET_KEY:
            print("✅ Stripe keys loaded successfully")
            print(f"   Public key: {self.STRIPE_PUBLIC_KEY[:15]}...")
        else:
            print("⚠️  Stripe keys not found in environment")

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    
    TEST_DIR = Config.basedir / 'test_temp'
    UPLOAD_BASE_DIR = TEST_DIR / 'uploads'
    UPLOAD_PATHS = {
        'products': str(UPLOAD_BASE_DIR / 'products'),
        'categories': str(UPLOAD_BASE_DIR / 'categories'),
        'users': str(UPLOAD_BASE_DIR / 'users'),
        'temp': str(UPLOAD_BASE_DIR / 'temp'),
        'documents': str(UPLOAD_BASE_DIR / 'documents'),
    }
    LOGS_DIR = TEST_DIR / 'logs'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'
    
    # Override database URI to use DATABASE_URL (PostgreSQL on Render)
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri and 'postgres' in db_uri and 'sslmode' not in db_uri:
        # Add sslmode=require for Render PostgreSQL
        db_uri += '?sslmode=require'
    SQLALCHEMY_DATABASE_URI = db_uri or Config.DEFAULT_DATABASE_URI
    
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')  # Redis would require paid add‑on
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', None)
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SSL_STRICT = True
    LOG_LEVEL = 'WARNING'
    
    def __init__(self):
        if not self.STRIPE_PUBLIC_KEY or not self.STRIPE_SECRET_KEY:
            print("⚠️  WARNING: STRIPE_PUBLIC_KEY or STRIPE_SECRET_KEY not set")
        else:
            if self.STRIPE_PUBLIC_KEY.startswith('pk_test_'):
                print("⚠️  WARNING: Using Stripe TEST keys in production!")
            elif self.STRIPE_PUBLIC_KEY.startswith('pk_live_'):
                print("✅ Stripe LIVE keys configured")
        
        # Warn about upload persistence
        print("ℹ️  Uploads are stored locally. For production, use cloud storage (S3/Cloudinary).")
        print(f"ℹ️  Database URI: {self.SQLALCHEMY_DATABASE_URI[:50]}...")


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])


def check_stripe_config():
    """Utility function to check Stripe configuration."""
    stripe_key = os.environ.get('STRIPE_PUBLIC_KEY')
    stripe_secret = os.environ.get('STRIPE_SECRET_KEY')
    
    print("\n" + "=" * 50)
    print("STRIPE CONFIGURATION CHECK")
    print("=" * 50)
    
    if stripe_key:
        if stripe_key.startswith('pk_test_'):
            print("✅ Stripe Public Key: TEST MODE")
            print(f"   {stripe_key[:15]}...{stripe_key[-10:]}")
        elif stripe_key.startswith('pk_live_'):
            print("⚠️  Stripe Public Key: LIVE MODE")
            print(f"   {stripe_key[:15]}...{stripe_key[-10:]}")
        else:
            print("❌ Stripe Public Key: Invalid format")
    else:
        print("❌ Stripe Public Key: Not found")
    
    if stripe_secret:
        if stripe_secret.startswith('sk_test_'):
            print("✅ Stripe Secret Key: TEST MODE")
            print(f"   {stripe_secret[:15]}...{stripe_secret[-10:]}")
        elif stripe_secret.startswith('sk_live_'):
            print("⚠️  Stripe Secret Key: LIVE MODE")
            print(f"   {stripe_secret[:15]}...{stripe_secret[-10:]}")
        else:
            print("❌ Stripe Secret Key: Invalid format")
    else:
        print("❌ Stripe Secret Key: Not found")
    
    print("=" * 50)
    return stripe_key is not None and stripe_secret is not None


# Run check if this file is executed directly
if __name__ == '__main__':
    check_stripe_config()
    
    print("\n" + "=" * 50)
    print("CONFIGURATION SUMMARY")
    print("=" * 50)
    env = os.environ.get('FLASK_ENV', 'development')
    print(f"Environment: {env}")
    print(f"Instance directory: {Config.INSTANCE_DIR}")
    print(f"Database: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"Upload base: {Config.UPLOAD_BASE_DIR}")
    print(f"Logs directory: {Config.LOGS_DIR}")
    print("=" * 50)