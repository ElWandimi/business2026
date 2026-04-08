# app/routes/main.py
# app/routes/main.py
from flask import Blueprint, render_template, request, jsonify, session, current_app, flash, redirect, url_for
from flask_login import login_required, current_user  # <-- ADD THIS
from app.models.product import Product, Category, Variant
from app.models.cart import Cart, CartItem
from app.models.wishlist import Wishlist
from app import db
from datetime import datetime
import random
import os
from flask import send_from_directory, current_app
from app.models.notification import Notification


bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page with featured products and categories."""
    # Try to get featured products first
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    # If none, get any active products (latest)
    if not featured_products:
        featured_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    
    categories = Category.query.filter_by(is_active=True).limit(6).all()
    new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    
    return render_template('index.html',
                         featured_products=featured_products,
                         categories=categories,
                         new_arrivals=new_arrivals)

@bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page with variant selection."""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    variants = Variant.query.filter_by(product_id=product.id, is_active=True).all()
    
    related = Product.query.filter_by(category_id=product.category_id, is_active=True)\
                           .filter(Product.id != product.id)\
                           .limit(4).all()
    
    return render_template('product_detail.html',
                         product=product,
                         variants=variants,
                         related=related)

@bp.route('/category/<slug>')
def category(slug):
    """Category listing page."""
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    
    query = Product.query.filter_by(category_id=category.id, is_active=True)
    
    if sort == 'price_asc':
        query = query.order_by(Product.base_price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.base_price.desc())
    elif sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    products = pagination.items
    
    return render_template('category.html',
                         category=category,
                         products=products,
                         pagination=pagination,
                         sort=sort)

@bp.route('/search')
def search():
    """Search products."""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if q:
        products = Product.query.filter(
            Product.name.ilike(f'%{q}%') | 
            Product.description.ilike(f'%{q}%'),
            Product.is_active == True
        ).order_by(Product.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    else:
        products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    
    return render_template('search.html', products=products, q=q)

@bp.route('/products')
def products():
    """List all active products with pagination and sorting."""
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    query = Product.query.filter_by(is_active=True)
    
    if sort == 'price_asc':
        query = query.order_by(Product.base_price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.base_price.desc())
    elif sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    products = pagination.items
    
    # Get all categories for filter dropdown
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('products.html', 
                         products=products, 
                         pagination=pagination, 
                         sort=sort,
                         categories=categories)

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form submission."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # For now, just flash a success message
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@bp.route('/api/cart/count')
def api_cart_count():
    """Return cart item count as JSON (for frontend)."""
    from app.routes.cart import get_cart
    cart = get_cart()
    count = sum(item.quantity for item in cart.items)
    return jsonify({'count': count})

@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    print(f"Attempting to serve: {full_path}")
    if not os.path.exists(full_path):
        print("File does NOT exist!")
    else:
        print("File exists!")
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
@bp.route('/orders')
def orders():
    """Temporary placeholder for user orders page."""
    flash('Order history feature is coming soon!', 'info')
    return redirect(url_for('main.index'))

@bp.route('/set-currency/<curr>')
def set_currency(curr):
    allowed = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY', 'KES']  # Added KES
    if curr in allowed:
        session['currency'] = curr
        if current_user.is_authenticated:
            current_user.currency = curr
            db.session.commit()
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/unsubscribe/abandoned/<token>')
def unsubscribe_abandoned(token):
    """Unsubscribe from abandoned cart emails."""
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, max_age=31536000)  # 1 year
    except (BadSignature, SignatureExpired):
        flash('Invalid or expired unsubscribe link.', 'danger')
        return redirect(url_for('main.index'))
    user = User.query.get(user_id)
    if user:
        user.email_abandoned_cart_opt_out = True
        db.session.commit()
        flash('You have been unsubscribed from cart reminder emails.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('main.index'))

@bp.route('/gift-card', methods=['GET', 'POST'])
def gift_card():
    """Page to purchase a gift card."""
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        recipient_email = request.form.get('recipient_email', '').strip()
        if amount < 5:
            flash('Minimum gift card amount is $5.', 'danger')
            return redirect(url_for('main.gift_card'))
        
        # Create a unique code
        from app.models.gift_card import GiftCard
        code = GiftCard().generate_code()
        # Ensure uniqueness (simple loop)
        while GiftCard.query.filter_by(code=code).first():
            code = GiftCard().generate_code()
        
        gift_card = GiftCard(
            code=code,
            initial_balance=amount,
            current_balance=amount,
            created_by=current_user.id if current_user.is_authenticated else None,
            recipient_email=recipient_email if recipient_email else None,
            is_active=True
        )
        db.session.add(gift_card)
        db.session.commit()

        # If user is logged in, we could add to cart? For simplicity, we'll just display the code.
        flash(f'Gift card created! Code: {code}', 'success')
        # Optionally send email to recipient
        if recipient_email:
            try:
                from app.services.email import send_gift_card_email
                send_gift_card_email(recipient_email, code, amount, current_user.email if current_user.is_authenticated else 'Anonymous')
            except Exception as e:
                current_app.logger.error(f"Gift card email error: {e}")

        return redirect(url_for('main.gift_card'))
    return render_template('gift_card.html')

@bp.route('/api/notifications/unread')
@login_required
def unread_notifications():
    """Return unread notifications for the current user (JSON)."""
    notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False)\
                               .order_by(Notification.created_at.desc())\
                               .limit(5).all()
    return jsonify({
        'count': len(notifs),
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
        } for n in notifs]
    })

# ============ Static Page Placeholders ============
@bp.route('/faq')
def faq():
    flash('FAQ page is under construction.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/about')
def about():
    flash('About Us page is under construction.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/terms')
def terms():
    flash('Terms & Conditions page is under construction.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/privacy')
def privacy():
    flash('Privacy Policy page is under construction.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/shipping')
def shipping():
    flash('Shipping Information page is under construction.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/returns')
def returns():
    flash('Returns & Refunds page is under construction.', 'info')
    return redirect(url_for('main.index'))