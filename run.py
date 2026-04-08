"""
Business2026 Application Entry Point
Run this file to start the Flask development server.
For production, use gunicorn: gunicorn run:app
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env explicitly (useful for development)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app import create_app, db
from app.models import User, Product, Order, OrderItem, Cart, CartItem

# Create the Flask application instance
app = create_app()

# ============ SHELL CONTEXT ============
@app.shell_context_processor
def make_shell_context():
    """Make these objects available in the Flask shell."""
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Order': Order,
        'OrderItem': OrderItem,
        'Cart': Cart,
        'CartItem': CartItem
    }

# ============ CLI COMMANDS ============
@app.cli.command("init-db")
def init_db_command():
    """Initialize the database with tables."""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

@app.cli.command("create-admin")
def create_admin_command():
    """Create an admin user."""
    from getpass import getpass
    
    with app.app_context():
        print("📝 Create Admin User")
        print("-" * 40)
        
        username = input("Username [admin]: ").strip() or "admin"
        email = input("Email [admin@business2026.com]: ").strip() or "admin@business2026.com"
        password = getpass("Password: ")
        confirm = getpass("Confirm password: ")
        
        if password != confirm:
            print("❌ Passwords do not match!")
            return
        
        if len(password) < 6:
            print("❌ Password must be at least 6 characters!")
            return
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"❌ Email '{email}' already exists!")
            return
        
        admin = User(
            username=username,
            email=email,
            is_admin=True,
            is_active=True,
            is_verified=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin user '{username}' created successfully!")

@app.cli.command("list-routes")
def list_routes_command():
    """List all registered routes."""
    with app.app_context():
        print("📋 Registered Routes:")
        print("-" * 80)
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"{rule.endpoint:30s} {methods:20s} {rule}")
        print("-" * 80)

@app.cli.command("drop-db")
def drop_db_command():
    """Drop all database tables."""
    confirm = input("⚠️  This will delete ALL data. Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        with app.app_context():
            db.drop_all()
        print("✅ Database tables dropped successfully!")
    else:
        print("❌ Operation cancelled.")

# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return {"error": "Page not found"}, 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return {"error": "Internal server error"}, 500

# ============ REQUEST HANDLERS ============
@app.before_request
def before_request():
    """Do something before each request."""
    pass

@app.after_request
def after_request(response):
    """Do something after each request."""
    return response

# ============ TEMPLATE CONTEXT PROCESSORS ============
@app.context_processor
def utility_processor():
    """Make utility functions available in templates."""
    from datetime import datetime
    
    def now():
        return datetime.now()
    
    def format_currency(amount):
        """Format amount as currency."""
        return f"${amount:.2f}"
    
    def format_date(date, format='%Y-%m-%d'):
        """Format date."""
        if date:
            return date.strftime(format)
        return ''
    
    return dict(
        now=now,
        format_currency=format_currency,
        format_date=format_date
    )

# ============ DEVELOPMENT SERVER ============
if __name__ == '__main__':
    # Get configuration from environment variables
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    
    # Print startup banner
    print("=" * 60)
    print("🚀 Business2026 Application Starting...")
    print("=" * 60)
    print(f"📁 Project Root: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"🔧 Debug Mode: {'ON' if debug_mode else 'OFF'}")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📡 Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print("=" * 60)
    print("Available Flask Commands:")
    print("  • flask init-db      - Create database tables")
    print("  • flask create-admin - Create admin user")
    print("  • flask list-routes  - Show all routes")
    print("  • flask drop-db      - Drop all tables (careful!)")
    print("  • flask shell        - Open Flask shell")
    print("=" * 60)
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    
    # Run the application
    app.run(
        debug=debug_mode,
        host=host,
        port=port,
        threaded=True
    )