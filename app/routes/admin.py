"""
Admin routes for Business2026 application.
Handles admin dashboard, product management, order management, user management, reports, coupons, support, settings, admin users, notifications, and promotions.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.product import Product, Category, ProductImage, Variant
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.coupon import Coupon
from app.models.support import SupportConversation, SupportMessage, SupportRating
from app.models.settings import Settings
from app.models.notification import Notification
from app.models.abandoned_cart import AbandonedCart
from app.models.promotion import Promotion
from app.forms.admin import VariantForm
from app.services.email import send_email
from app.services.email import send_support_reply
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import os
import json
from werkzeug.utils import secure_filename
import uuid
import sys
import re
from app.utils.permissions import permission_required
from app.models.role import Role, Permission
from app.models.admin_log import AdminLog


bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ============ DASHBOARD ============
@bp.route('/')
@login_required
@admin_required
@permission_required('dashboard_access')
def dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total)).filter_by(payment_status='paid').scalar() or 0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_support = SupportConversation.query.order_by(SupportConversation.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         recent_support=recent_support)

# ============ PRODUCT MANAGEMENT ============
@bp.route('/products')
@login_required
@admin_required
@permission_required('product_management')
def products():
    page = request.args.get('page', 1, type=int)
    pagination = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    products = pagination.items
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, pagination=pagination, categories=categories)

@bp.route('/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('product_management')
def add_product():
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form['name'],
                slug=request.form['slug'],
                sku=request.form.get('sku'),
                description=request.form.get('description'),
                short_description=request.form.get('short_description'),
                base_price=float(request.form['base_price']),
                category_id=int(request.form['category_id']),
                brand=request.form.get('brand'),
                weight=float(request.form['weight']) if request.form.get('weight') else None,
                dimensions=request.form.get('dimensions'),
                is_featured='is_featured' in request.form,
                is_active='is_active' in request.form
            )
            
            db.session.add(product)
            db.session.flush()
            
            files = request.files.getlist('images')
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(upload_dir, exist_ok=True)
            
            for i, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    
                    image = ProductImage(
                        product_id=product.id,
                        image_url=f"/uploads/products/{filename}",
                        is_primary=(i == 0),
                        sort_order=i
                    )
                    db.session.add(image)
            
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
    
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/add_product.html', categories=categories)

@bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('product_management')
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.slug = request.form['slug']
            product.sku = request.form.get('sku')
            product.description = request.form.get('description')
            product.short_description = request.form.get('short_description')
            product.base_price = float(request.form['base_price'])
            product.category_id = int(request.form['category_id'])
            product.brand = request.form.get('brand')
            product.weight = float(request.form['weight']) if request.form.get('weight') else None
            product.dimensions = request.form.get('dimensions')
            product.is_featured = 'is_featured' in request.form
            product.is_active = 'is_active' in request.form
            product.updated_at = datetime.utcnow()
            
            files = request.files.getlist('images')
            if files and files[0] and files[0].filename:
                max_sort = db.session.query(db.func.max(ProductImage.sort_order)).filter_by(product_id=product.id).scalar() or -1
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
                os.makedirs(upload_dir, exist_ok=True)
                
                for i, file in enumerate(files):
                    if file and file.filename and allowed_file(file.filename):
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"{uuid.uuid4().hex}.{ext}"
                        filepath = os.path.join(upload_dir, filename)
                        file.save(filepath)
                        
                        image = ProductImage(
                            product_id=product.id,
                            image_url=f"/uploads/products/{filename}",
                            is_primary=False,
                            sort_order=max_sort + i + 1
                        )
                        db.session.add(image)
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/edit_product.html', product=product, categories=categories)

# ============ VARIANT MANAGEMENT ============
@bp.route('/product/<int:product_id>/variants', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('product_management')
def admin_product_variants(product_id):
    product = Product.query.get_or_404(product_id)
    form = VariantForm()
    
    if form.validate_on_submit():
        variant = Variant(
            product_id=product.id,
            sku=form.sku.data,
            size=form.size.data,
            color=form.color.data,
            color_code=form.color_code.data,
            price_adjustment=form.price_adjustment.data,
            stock=form.stock.data,
            image_url=form.image_url.data,
            is_active=True
        )
        db.session.add(variant)
        db.session.commit()
        flash('Variant added successfully', 'success')
        return redirect(url_for('admin.admin_product_variants', product_id=product.id))
    
    variants = Variant.query.filter_by(product_id=product.id).all()
    return render_template('admin/product_variants.html', product=product, variants=variants, form=form)

@bp.route('/variant/<int:variant_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('product_management')
def admin_edit_variant(variant_id):
    variant = Variant.query.get_or_404(variant_id)
    form = VariantForm(obj=variant)
    
    if form.validate_on_submit():
        variant.sku = form.sku.data
        variant.size = form.size.data
        variant.color = form.color.data
        variant.color_code = form.color_code.data
        variant.price_adjustment = form.price_adjustment.data
        variant.stock = form.stock.data
        variant.image_url = form.image_url.data
        variant.is_active = form.is_active.data
        db.session.commit()
        flash('Variant updated successfully', 'success')
        return redirect(url_for('admin.admin_product_variants', product_id=variant.product_id))
    
    return render_template('admin/edit_variant.html', form=form, variant=variant)

@bp.route('/variant/<int:variant_id>/delete', methods=['POST'])
@login_required
@admin_required
@permission_required('product_management')
def admin_delete_variant(variant_id):
    variant = Variant.query.get_or_404(variant_id)
    product_id = variant.product_id
    db.session.delete(variant)
    db.session.commit()
    flash('Variant deleted', 'success')
    return redirect(url_for('admin.admin_product_variants', product_id=product_id))

@bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
@permission_required('product_management')
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ ORDER MANAGEMENT ============
@bp.route('/orders')
@login_required
@admin_required
@permission_required('order_management')
def orders():
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Order.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    orders = pagination.items
    
    return render_template('admin/orders.html', 
                         orders=orders,
                         pagination=pagination,
                         current_status=status)

@bp.route('/order/<int:order_id>')
@login_required
@admin_required
@permission_required('order_management')
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@bp.route('/order/<int:order_id>/update', methods=['POST'])
@login_required
@admin_required
@permission_required('order_management')
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    old_status = order.status
    order.status = request.form['status']
    order.payment_status = request.form['payment_status']
    order.tracking_number = request.form.get('tracking_number')
    order.carrier = request.form.get('carrier')
    db.session.commit()
    
    # ===== NOTIFICATION: Order status update =====
    if order.user_id:
        try:
            from app.models.notification import Notification
            notif = Notification(
                user_id=order.user_id,
                type='order_status',
                title=f'Order #{order.order_number} status updated',
                message=f'New status: {order.status}',
                link=url_for('auth.order_detail', order_id=order.id)
            )
            db.session.add(notif)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to create order status notification: {e}")
    
    if old_status != 'delivered' and order.status == 'delivered':
        try:
            from app.services.email import send_order_status_update
            send_order_status_update(order)
        except Exception as e:
            current_app.logger.error(f"Delivery email error: {e}")
    
    flash('Order updated successfully!', 'success')
    return redirect(url_for('admin.order_detail', order_id=order.id))

# ============ USER MANAGEMENT ============
@bp.route('/users')
@login_required
@admin_required
@permission_required('user_management')
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@bp.route('/user/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
@permission_required('user_management')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot deactivate your own account.'})
    
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True, 'message': f'User {"activated" if user.is_active else "deactivated"} successfully!'})

# ============ CATEGORY MANAGEMENT ============
@bp.route('/categories')
@login_required
@admin_required
@permission_required('category_management')
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/category/add', methods=['POST'])
@login_required
@admin_required
@permission_required('category_management')
def add_category():
    try:
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        if not name or not slug:
            return jsonify({'success': False, 'message': 'Name and slug are required'})
        existing = Category.query.filter_by(slug=slug).first()
        if existing:
            return jsonify({'success': False, 'message': 'Slug already exists'})
        category = Category(name=name, slug=slug, description=description, is_active=True)
        db.session.add(category)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Category added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/category/<int:category_id>/get', methods=['GET'])
@login_required
@admin_required
@permission_required('category_management')
def get_category(category_id):
    category = Category.query.get_or_404(category_id)
    return jsonify({
        'success': True,
        'category': {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description or ''
        }
    })

@bp.route('/category/<int:category_id>/edit', methods=['POST'])
@login_required
@admin_required
@permission_required('category_management')
def edit_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        existing = Category.query.filter(Category.slug == slug, Category.id != category_id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Slug already exists'})
        category.name = name
        category.slug = slug
        category.description = description
        db.session.commit()
        return jsonify({'success': True, 'message': 'Category updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/category/<int:category_id>/toggle', methods=['POST'])
@login_required
@admin_required
@permission_required('category_management')
def toggle_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        category.is_active = not category.is_active
        db.session.commit()
        return jsonify({'success': True, 'message': f'Category {"activated" if category.is_active else "deactivated"}', 'is_active': category.is_active})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
@permission_required('category_management')
def delete_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        if category.products.count() > 0:
            return jsonify({'success': False, 'message': 'Cannot delete category with products'}), 400
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Category deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ COUPON MANAGEMENT ============
@bp.route('/coupons')
@login_required
@admin_required
@permission_required('coupon_management')
def coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

@bp.route('/coupon/add', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('coupon_management')
def add_coupon():
    if request.method == 'POST':
        try:
            coupon = Coupon(
                code=request.form['code'].upper(),
                description=request.form.get('description'),
                discount_type=request.form['discount_type'],
                discount_amount=float(request.form['discount_amount']),
                minimum_order=float(request.form.get('minimum_order', 0)),
                max_uses=int(request.form.get('max_uses', 0)),
                expires_at=datetime.strptime(request.form['expires_at'], '%Y-%m-%d') if request.form.get('expires_at') else None
            )
            db.session.add(coupon)
            db.session.commit()
            flash('Coupon added successfully', 'success')
            return redirect(url_for('admin.coupons'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/coupon_form.html', coupon=None)

@bp.route('/coupon/<int:coupon_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('coupon_management')
def edit_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    if request.method == 'POST':
        try:
            coupon.code = request.form['code'].upper()
            coupon.description = request.form.get('description')
            coupon.discount_type = request.form['discount_type']
            coupon.discount_amount = float(request.form['discount_amount'])
            coupon.minimum_order = float(request.form.get('minimum_order', 0))
            coupon.max_uses = int(request.form.get('max_uses', 0))
            coupon.expires_at = datetime.strptime(request.form['expires_at'], '%Y-%m-%d') if request.form.get('expires_at') else None
            db.session.commit()
            flash('Coupon updated successfully', 'success')
            return redirect(url_for('admin.coupons'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/coupon_form.html', coupon=coupon)

@bp.route('/coupon/<int:coupon_id>/toggle', methods=['POST'])
@login_required
@admin_required
@permission_required('coupon_management')
def toggle_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': coupon.is_active})

@bp.route('/coupon/<int:coupon_id>/delete', methods=['POST'])
@login_required
@admin_required
@permission_required('coupon_management')
def delete_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    return jsonify({'success': True})

from app.models.promotion import Promotion
from flask import render_template_string

@bp.route('/coupon/generate-code')
@login_required
@admin_required
@permission_required('coupon_management')
def generate_coupon_code():
    from app.utils.helpers import generate_coupon_code
    from app.models.coupon import Coupon
    length = request.args.get('length', 8, type=int)
    prefix = request.args.get('prefix', '')
    suffix = request.args.get('suffix', '')
    attempts = 0
    while attempts < 10:
        code = generate_coupon_code(length, prefix, suffix)
        if not Coupon.query.filter_by(code=code).first():
            return jsonify({'code': code})
        attempts += 1
    # fallback – if all attempts fail, still return a code
    return jsonify({'code': generate_coupon_code(length, prefix, suffix)})

# ============ PROMOTIONS ============
@bp.route('/promotions')
@login_required
@admin_required
@permission_required('coupon_management')
def promotions():
    """List all sent promotions."""
    promos = Promotion.query.order_by(Promotion.sent_at.desc()).all()
    return render_template('admin/promotions.html', promotions=promos)

@bp.route('/promotion/new', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('coupon_management')
def new_promotion():
    """Create and send a new promotional email."""
    if request.method == 'POST':
        subject = request.form['subject']
        html_content = request.form['html_content']
        segment = request.form.get('segment', 'all')
        
        # Determine recipients based on segment
        query = User.query.filter_by(is_active=True)
        if segment == 'verified':
            query = query.filter_by(is_verified=True)
        elif segment == 'has_orders':
            query = query.filter(User.orders.any())
        # 'all' includes all active users
        
        users = query.all()
        recipient_count = len(users)
        
        # Create promotion record
        promo = Promotion(
            subject=subject,
            html_content=html_content,
            segment=segment,
            recipient_count=recipient_count,
            created_by=current_user.id
        )
        db.session.add(promo)
        db.session.commit()
        
        # Send emails and create notifications
        sent_count = 0
        for user in users:
            if not user.email_abandoned_cart_opt_out:
                unsubscribe_url = url_for('main.unsubscribe_abandoned', token=user.generate_unsubscribe_token(), _external=True)
                # Render HTML with user context
                personalized_html = render_template_string(
                    html_content,
                    user=user,
                    unsubscribe_url=unsubscribe_url,
                    site_url=current_app.config.get('SITE_URL', 'http://localhost:5001')
                )
                # Create plain text version (strip HTML tags)
                plain_text = re.sub('<[^<]+?>', '', html_content)
                # Send email
                send_email(user.email, subject, plain_text, personalized_html)
                sent_count += 1

                # ===== NOTIFICATION: Promotional email =====
                notif = Notification(
                    user_id=user.id,
                    type='promotion',
                    title=subject,
                    message=plain_text[:100] + ('...' if len(plain_text) > 100 else ''),
                    link=url_for('main.products')
                )
                db.session.add(notif)
        
        # Commit all notifications after the loop
        db.session.commit()
        
        flash(f'Promotion sent to {sent_count} users.', 'success')
        return redirect(url_for('admin.promotions'))
    
    return render_template('admin/promotion_form.html')
    
# ============ REPORTS ============
@bp.route('/reports')
@login_required
@admin_required
@permission_required('report_access')
def reports():
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    sales_data = db.session.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.total).label('revenue')
    ).filter(
        Order.created_at >= start_date,
        Order.payment_status == 'paid'
    ).group_by(func.date(Order.created_at)).all()
    
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
    ).join(Variant, Variant.id == OrderItem.variant_id
    ).join(Product, Product.id == Variant.product_id
    ).join(Order, Order.id == OrderItem.order_id
    ).filter(
        Order.payment_status == 'paid',
        Order.created_at >= start_date
    ).group_by(Product.id).order_by(desc('total_sold')).limit(10).all()
    
    total_orders = Order.query.filter(
        Order.created_at >= start_date,
        Order.payment_status == 'paid'
    ).count()
    
    total_revenue = db.session.query(func.sum(Order.total)).filter(
        Order.created_at >= start_date,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    orders_by_status = {
        'pending': Order.query.filter(Order.created_at >= start_date, Order.status == 'pending').count(),
        'processing': Order.query.filter(Order.created_at >= start_date, Order.status == 'processing').count(),
        'shipped': Order.query.filter(Order.created_at >= start_date, Order.status == 'shipped').count(),
        'delivered': Order.query.filter(Order.created_at >= start_date, Order.status == 'delivered').count(),
        'cancelled': Order.query.filter(Order.created_at >= start_date, Order.status == 'cancelled').count(),
    }
    
    return render_template('admin/reports.html',
                         days=days,
                         sales_data=sales_data,
                         top_products=top_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         average_order_value=average_order_value,
                         orders_by_status=orders_by_status)

# ============ SETTINGS ============
@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('dashboard_access')
def settings():
    """Manage site settings."""
    settings = Settings.get_settings()
    
    if request.method == 'POST':
        try:
            settings.site_name = request.form.get('site_name')
            settings.site_url = request.form.get('site_url')
            settings.admin_email = request.form.get('admin_email')
            settings.currency_code = request.form.get('currency_code')
            settings.currency_symbol = request.form.get('currency_symbol')
            settings.tax_rate = float(request.form.get('tax_rate', 0))
            settings.tax_included = 'tax_included' in request.form
            settings.order_prefix = request.form.get('order_prefix')
            settings.low_stock_threshold = int(request.form.get('low_stock_threshold', 5))
            settings.enable_reviews = 'enable_reviews' in request.form
            settings.enable_wishlist = 'enable_wishlist' in request.form
            settings.enable_gift_cards = 'enable_gift_cards' in request.form
            db.session.commit()
            flash('Settings updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {e}', 'danger')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=settings)

# ============ ADMIN USERS ============
@bp.route('/admin-users')
@login_required
@admin_required
@permission_required('role_management')
def admin_users():
    """List all admin users (only for super admins)."""
    if not current_user.is_super_admin:
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    admins = User.query.filter_by(is_admin=True).order_by(User.created_at.desc()).all()
    return render_template('admin/admin_users.html', admins=admins)

@bp.route('/admin-users/add', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('role_management')
def add_admin_user():
    """Add a new admin user (super admin only)."""
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_super_admin = 'is_super_admin' in request.form
        
        if not username or not email or not password:
            flash('All fields required.', 'danger')
            return redirect(url_for('admin.add_admin_user'))
        
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('admin.add_admin_user'))
        
        user = User(
            username=username,
            email=email,
            is_admin=True,
            is_super_admin=is_super_admin
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Admin user added successfully.', 'success')
        return redirect(url_for('admin.admin_users'))
    
    return render_template('admin/add_admin_user.html')

@bp.route('/admin-users/<int:user_id>/toggle-super', methods=['POST'])
@login_required
@admin_required
@permission_required('role_management')
def toggle_super_admin(user_id):
    """Toggle super admin status (only super admins can do this)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot change your own status'}), 400
    
    user.is_super_admin = not user.is_super_admin
    db.session.commit()
    return jsonify({'success': True, 'is_super_admin': user.is_super_admin})

@bp.route('/admin-users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
@permission_required('role_management')
def delete_admin_user(user_id):
    """Delete an admin user (super admin only, cannot delete self)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete yourself'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

# ============ NOTIFICATIONS API ============
@bp.route('/notifications/unread')
@login_required
@admin_required
@permission_required('dashboard_access')
def get_unread_notifications():
    """Return unread notifications for the current admin (or all broadcast)."""
    notifs = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None)
    ).filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(10).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'link': n.link,
        'created_at': n.created_at.isoformat()
    } for n in notifs])

@bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
@admin_required
@permission_required('dashboard_access')
def mark_notification_read(notif_id):
    """Mark a notification as read."""
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id and notif.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/notifications')
@login_required
@admin_required
@permission_required('dashboard_access')
def all_notifications():
    notifs = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None)
    ).order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', notifications=notifs)

# ============ SUPPORT DASHBOARD ============
@bp.route('/support')
@login_required
@admin_required
@permission_required('support_management')
def support_dashboard():
    """Display all support conversations with optional filters."""
    filter_status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = SupportConversation.query
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    if search:
        query = query.filter(
            (SupportConversation.name.ilike(f'%{search}%')) |
            (SupportConversation.email.ilike(f'%{search}%'))
        )
    conversations = query.order_by(SupportConversation.updated_at.desc()).all()
    return render_template('admin/support.html', conversations=conversations, filter_status=filter_status, search=search)

@bp.route('/support/messages/<int:conv_id>')
@login_required
@admin_required
@permission_required('support_management')
def support_messages(conv_id):
    """Get all messages for a conversation (AJAX)."""
    messages = SupportMessage.query.filter_by(conversation_id=conv_id).order_by(SupportMessage.created_at.asc()).all()
    return jsonify({'messages': [{
        'id': m.id,
        'sender': m.sender,
        'message': m.message,
        'created_at': m.created_at.isoformat()
    } for m in messages]})

@bp.route('/support/reply', methods=['POST'])
@login_required
@admin_required
@permission_required('support_management')
def support_reply():
    """Admin replies to a support conversation."""
    data = request.get_json()
    conv_id = data.get('conversation_id')
    message = data.get('message')
    
    if not conv_id or not message:
        return jsonify({'success': False, 'error': 'Missing conversation_id or message'}), 400
    
    conv = SupportConversation.query.get(conv_id)
    if not conv:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404
    
    # Don't allow replies if conversation is closed
    if conv.status == 'closed':
        return jsonify({'success': False, 'error': 'Conversation is closed'}), 400
    
    # Save reply
    msg = SupportMessage(conversation_id=conv.id, sender='support', message=message)
    db.session.add(msg)
    conv.updated_at = datetime.utcnow()
    if conv.status == 'open':
        conv.status = 'pending'
    db.session.commit()
    
    try:
        send_support_reply(conv, message)
    except Exception as e:
        current_app.logger.error(f"Failed to send support reply email: {e}")
    
    return jsonify({'success': True})

@bp.route('/support/<int:conv_id>/status', methods=['POST'])
@login_required
@admin_required
@permission_required('support_management')
def update_support_status(conv_id):
    data = request.get_json()
    status = data.get('status')
    if status not in ['open', 'pending', 'closed']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    conv = SupportConversation.query.get_or_404(conv_id)
    conv.status = status
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'status': status})

# For user rating
@bp.route('/support/<int:conv_id>/rate', methods=['POST'])
def user_rate_conversation(conv_id):
    data = request.get_json()
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    
    if not rating or not (1 <= rating <= 5):
        return jsonify({'success': False, 'error': 'Rating must be 1-5'}), 400
    
    conv = SupportConversation.query.get(conv_id)
    if not conv:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404
    
    if conv.rating:
        return jsonify({'success': False, 'error': 'Already rated'}), 400
    
    rating_obj = SupportRating(conversation_id=conv.id, rating=rating, feedback=feedback)
    db.session.add(rating_obj)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/product/image/<int:image_id>/delete', methods=['POST'])
@login_required
@admin_required
@permission_required('product_management')
def delete_product_image(image_id):
    try:
        image = ProductImage.query.get_or_404(image_id)
        db.session.delete(image)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Image deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ INVENTORY ============
@bp.route('/inventory')
@login_required
@admin_required
@permission_required('inventory_management')
def inventory():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    return render_template('admin/inventory.html', products=products)

@bp.route('/variant/<int:variant_id>/update-stock', methods=['POST'])
@login_required
@admin_required
@permission_required('inventory_management')
def update_variant_stock(variant_id):
    data = request.get_json()
    new_stock = data.get('stock')
    if new_stock is None or not isinstance(new_stock, int) or new_stock < 0:
        return jsonify({'success': False, 'message': 'Invalid stock value'}), 400

    variant = Variant.query.get_or_404(variant_id)
    variant.stock = new_stock
    db.session.commit()
    return jsonify({'success': True})

# ============ ABANDONED CARTS ============
@bp.route('/abandoned-carts')
@login_required
@admin_required
@permission_required('order_management')
def abandoned_carts():
    page = request.args.get('page', 1, type=int)
    pagination = AbandonedCart.query.order_by(AbandonedCart.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/abandoned_carts.html', pagination=pagination)

# ============ GIFT CARDS ============
from app.models.gift_card import GiftCard

@bp.route('/gift-cards')
@login_required
@admin_required
@permission_required('gift_card_management')
def gift_cards():
    page = request.args.get('page', 1, type=int)
    pagination = GiftCard.query.order_by(GiftCard.purchased_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/gift_cards.html', pagination=pagination)

@bp.route('/gift-card/add', methods=['GET', 'POST'])
@login_required
@admin_required
@permission_required('gift_card_management')
def add_gift_card():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        code = request.form.get('code', '').strip().upper()
        recipient = request.form.get('recipient_email') or None
        expires = request.form.get('expires_at')
        expires_at = datetime.strptime(expires, '%Y-%m-%d') if expires else None

        if not code:
            code = GiftCard().generate_code()
            while GiftCard.query.filter_by(code=code).first():
                code = GiftCard().generate_code()

        gift = GiftCard(
            code=code,
            initial_balance=amount,
            current_balance=amount,
            created_by=current_user.id,
            recipient_email=recipient,
            expires_at=expires_at,
            is_active=True
        )
        db.session.add(gift)
        db.session.commit()
        flash(f'Gift card {code} created.', 'success')
        return redirect(url_for('admin.gift_cards'))
    return render_template('admin/gift_card_form.html')

@bp.route('/gift-card/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
@permission_required('gift_card_management')
def toggle_gift_card(id):
    gift = GiftCard.query.get_or_404(id)
    gift.is_active = not gift.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': gift.is_active})

# ============ ADMIN MANAGEMENT (SUPER ADMIN ONLY) ============
@bp.route('/admin-management')
@login_required
@admin_required
def admin_management():
    """List all admin users (super admin only)."""
    if not current_user.is_super_admin:
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get all users who are admins OR have roles/permissions
    admins = User.query.filter(
        (User.is_admin == True) | (User.roles.any())
    ).order_by(User.created_at.desc()).all()
    roles = Role.query.all()
    permissions = Permission.query.all()
    
    return render_template('admin/admin_management.html',
                           admins=admins,
                           roles=roles,
                           permissions=permissions)

@bp.route('/create-admin-user', methods=['POST'])
@login_required
@admin_required
def create_admin_user():
    """Create a new admin user (super admin only)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin_flag = 'is_admin' in request.form
    role_ids = request.form.getlist('roles')
    perm_ids = request.form.getlist('permissions')
    
    # Validate
    if not username or not email or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin.admin_management'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin.admin_management'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'danger')
        return redirect(url_for('admin.admin_management'))
    
    # Create user
    user = User(
        username=username,
        email=email,
        is_admin=is_admin_flag,
        is_super_admin=False,
        is_verified=True,
        email_verified_at=datetime.utcnow()
    )
    user.set_password(password)
    
    # Assign roles
    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles
    
    # Assign direct permissions
    if perm_ids:
        perms = Permission.query.filter(Permission.id.in_(perm_ids)).all()
        user.permissions = perms
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'Admin user {username} created successfully', 'success')
    return redirect(url_for('admin.admin_management'))

@bp.route('/admin-management/<int:user_id>/get', methods=['GET'])
@login_required
@admin_required
def get_admin_user(user_id):
    """Return user data for editing (super admin only)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Prepare roles with selection status
    all_roles = Role.query.all()
    roles_data = []
    for role in all_roles:
        roles_data.append({
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'selected': role in user.roles
        })
    
    # Prepare permissions with selection status
    all_perms = Permission.query.all()
    perms_data = []
    for perm in all_perms:
        perms_data.append({
            'id': perm.id,
            'name': perm.name,
            'description': perm.description,
            'selected': perm in user.permissions
        })
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'roles': roles_data,
        'permissions': perms_data
    })

@bp.route('/admin-management/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_admin_user(user_id):
    """Update user roles and permissions (super admin only)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    is_admin_flag = 'is_admin' in request.form
    role_ids = request.form.getlist('roles')
    perm_ids = request.form.getlist('permissions')
    
    user.is_admin = is_admin_flag
    
    # Update roles
    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles
    else:
        user.roles = []
    
    # Update permissions
    if perm_ids:
        perms = Permission.query.filter(Permission.id.in_(perm_ids)).all()
        user.permissions = perms
    else:
        user.permissions = []
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'User updated successfully'})

@bp.route('/admin-management/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_admin_user(user_id):
    """Activate/deactivate a user (super admin only)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({'success': True, 'active': user.is_active})

@bp.route('/admin-management/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_managed_user(user_id):
    """Delete a user (super admin only)."""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'})
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@bp.route('/admin-logs')
@login_required
@admin_required
@permission_required('role_management')
def admin_logs():
    page = request.args.get('page', 1, type=int)
    pagination = AdminLog.query.order_by(AdminLog.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/admin_logs.html', pagination=pagination)