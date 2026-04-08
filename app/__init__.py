from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_babel import Babel
from flask import session, request
from flask_login import current_user

# Initialize extensions (no imports from app.models yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Import models now that db and login_manager are available
    with app.app_context():
        from app.models import User  # This will import all models via __init__.py

    # Define user loader (after User model is imported)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Babel setup
    babel = Babel(app)

    def get_locale():
        from flask_login import current_user
        if current_user.is_authenticated and hasattr(current_user, 'language') and current_user.language:
            return current_user.language
        return session.get('language', request.accept_languages.best_match(['en', 'es', 'fr']))

    app.config['BABEL_LOCALE_SELECTOR'] = get_locale

    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.routes import main, auth, admin, cart, payment, reviews, wishlist, test, support
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(cart.bp, url_prefix='/cart')
    app.register_blueprint(payment.bp, url_prefix='/payment')
    app.register_blueprint(reviews.bp, url_prefix='/reviews')
    app.register_blueprint(wishlist.bp, url_prefix='/wishlist')
    app.register_blueprint(test.bp, url_prefix='/test')
    app.register_blueprint(support.bp, url_prefix='/support')

    # Setup logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/business2026.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Business2026 startup')

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'users'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'categories'), exist_ok=True)

    # Register currency filter
    from app.utils.currency import format_currency
    app.jinja_env.filters['currency'] = format_currency

    # Register CLI commands
    from app import cli
    app.cli.add_command(cli.send_abandoned_cart_emails)
    app.cli.add_command(cli.seed_roles_permissions)

    # Context processor for support ticket count
    @app.context_processor
    def utility_processor():
        def unresolved_support_count():
            from app.models.support import SupportConversation  # import here to avoid circular import
            if current_user.is_authenticated:
                return SupportConversation.query.filter(
                    SupportConversation.user_id == current_user.id,
                    SupportConversation.status.in_(['open', 'pending'])
                ).count()
            return 0
        return dict(unresolved_support_count=unresolved_support_count)

    return app