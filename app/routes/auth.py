# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.cart import Cart
from app.models.order import Order
from app.models.address import Address
from app.models.payment_method import PaymentMethod
from app.forms.address import AddressForm
from app.forms.profile import ProfileForm
from app.services.stripe import create_stripe_customer, add_payment_method
from app.services.email import send_verification_email, send_password_reset_email  # NEW
import stripe
from datetime import datetime
import uuid
from app.models.notification import Notification
from app.forms.auth import RegistrationForm
from app.models.cart import Cart
from flask import session





bp = Blueprint('auth', __name__)

# ============ EXISTING AUTH ROUTES ============
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('This account has been deactivated.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user, remember=remember)
            user.update_last_login(request.remote_addr)

            # Merge guest cart into user's cart
            guest_session_id = session.pop('cart_session_id', None)
            if guest_session_id:
                guest_cart = Cart.query.filter_by(session_id=guest_session_id).first()
                if guest_cart:
                    user_cart = user.get_cart_or_create()
                    for item in guest_cart.items:
                        # Check if product already in user's cart
                        existing = next(
                            (i for i in user_cart.items if i.product_id == item.product_id and i.variant_id == item.variant_id),
                            None
                        )
                        if existing:
                            existing.quantity += item.quantity
                        else:
                            item.cart_id = user_cart.id
                            db.session.add(item)
                    db.session.delete(guest_cart)
                    db.session.commit()

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Create user with data from the form
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()

        # Create a cart for the new user
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()

        # ===== NOTIFICATION: New user registration =====
        try:
            from app.models.notification import Notification
            notif = Notification(
                type='new_user',
                title=f'New user registered: {user.username}',
                message=f'Email: {user.email}',
                link=url_for('admin.users')
            )
            db.session.add(notif)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to create registration notification: {e}")

        # ===== EMAIL VERIFICATION =====
        try:
            send_verification_email(user)
        except Exception as e:
            current_app.logger.error(f"Verification email error: {e}")

        # ===== WELCOME EMAIL =====
        try:
            from app.services.email import send_welcome_email
            send_welcome_email(user)
        except Exception as e:
            current_app.logger.error(f"Welcome email error: {e}")

        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))

    # GET request (or validation failure) – render the form
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ============ EMAIL VERIFICATION ============
@bp.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('main.index'))

    if user.verify_email(token):
        flash('Your email has been verified. You can now log in.', 'success')
    else:
        flash('Verification failed. The link may have expired.', 'danger')
    return redirect(url_for('auth.login'))


# ============ PASSWORD RESET ============
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                send_password_reset_email(user)
            except Exception as e:
                current_app.logger.error(f"Password reset email error: {e}")
        # Always show same message to prevent email enumeration
        flash('If that email is registered, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(reset_password_token=token).first()
    if not user or not user.verify_reset_password_token(token):
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not password or password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        user.reset_password_token = None
        user.reset_password_expires = None
        db.session.commit()
        flash('Your password has been reset. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ============ PROFILE MANAGEMENT ============
@bp.route('/profile')
@login_required
def profile():
    """Main profile page with tabs."""
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(10).all()
    return render_template('auth/profile.html',
                         user=current_user,
                         addresses=addresses,
                         payment_methods=payment_methods,
                         orders=orders)


@bp.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data or current_user.first_name
        current_user.last_name = form.last_name.data or current_user.last_name
        current_user.phone = form.phone.data or current_user.phone

        if form.new_password.data:
            # Optionally verify current password (if you want)
            if form.current_password.data and current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
            else:
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))

        db.session.commit()
        flash('Profile updated successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('auth.profile'))


# ============ ADDRESS MANAGEMENT ============
@bp.route('/profile/address/add', methods=['GET', 'POST'])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        # If setting as default, unset existing default for same type
        if form.is_default.data:
            Address.query.filter_by(
                user_id=current_user.id,
                address_type=form.address_type.data,
                is_default=True
            ).update({'is_default': False})

        address = Address(
            user_id=current_user.id,
            address_type=form.address_type.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            company=form.company.data,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            phone=form.phone.data,
            is_default=form.is_default.data
        )
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/address_form.html', form=form, title='Add Address')


@bp.route('/profile/address/<int:address_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.profile'))

    form = AddressForm(obj=address)
    if form.validate_on_submit():
        # If setting as default and wasn't default, unset others
        if form.is_default.data and not address.is_default:
            Address.query.filter_by(
                user_id=current_user.id,
                address_type=form.address_type.data,
                is_default=True
            ).update({'is_default': False})

        address.address_type = form.address_type.data
        address.first_name = form.first_name.data
        address.last_name = form.last_name.data
        address.company = form.company.data
        address.address_line1 = form.address_line1.data
        address.address_line2 = form.address_line2.data
        address.city = form.city.data
        address.state = form.state.data
        address.postal_code = form.postal_code.data
        address.country = form.country.data
        address.phone = form.phone.data
        address.is_default = form.is_default.data

        db.session.commit()
        flash('Address updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/address_form.html', form=form, title='Edit Address')


@bp.route('/profile/address/<int:address_id>/delete', methods=['POST'])
@login_required
def delete_address(address_id):
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    was_default = address.is_default
    address_type = address.address_type
    db.session.delete(address)

    # If deleted address was default, set another as default if exists
    if was_default:
        new_default = Address.query.filter_by(
            user_id=current_user.id,
            address_type=address_type
        ).first()
        if new_default:
            new_default.is_default = True

    db.session.commit()
    return jsonify({'success': True, 'message': 'Address deleted'})


# ============ PAYMENT METHODS ============
@bp.route('/profile/payment/add', methods=['POST'])
@login_required
def add_payment_method():
    """Add a payment method via Stripe (requires frontend token)."""
    data = request.get_json()
    payment_method_id = data.get('payment_method_id')
    if not payment_method_id:
        return jsonify({'success': False, 'message': 'Missing payment method ID'}), 400

    # Create or retrieve Stripe customer
    stripe_customer_id = current_user.stripe_customer_id
    if not stripe_customer_id:
        try:
            customer = create_stripe_customer(current_user)
            current_user.stripe_customer_id = customer.id
            db.session.commit()
            stripe_customer_id = customer.id
        except stripe.error.StripeError as e:
            return jsonify({'success': False, 'message': str(e)}), 400

    # Attach payment method to customer
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        payment_method.attach(customer=stripe_customer_id)

        # Set as default if none exists
        is_default = PaymentMethod.query.filter_by(user_id=current_user.id).count() == 0

        pm = PaymentMethod(
            user_id=current_user.id,
            stripe_payment_method_id=payment_method_id,
            stripe_customer_id=stripe_customer_id,
            card_brand=payment_method.card.brand,
            card_last4=payment_method.card.last4,
            card_exp_month=payment_method.card.exp_month,
            card_exp_year=payment_method.card.exp_year,
            is_default=is_default
        )
        db.session.add(pm)
        db.session.commit()

        return jsonify({'success': True, 'payment_method_id': pm.id})
    except stripe.error.StripeError as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/profile/payment/<int:pm_id>/default', methods=['POST'])
@login_required
def set_default_payment(pm_id):
    pm = PaymentMethod.query.get_or_404(pm_id)
    if pm.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Unset existing default
    PaymentMethod.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    pm.is_default = True
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/profile/payment/<int:pm_id>/delete', methods=['POST'])
@login_required
def delete_payment_method(pm_id):
    pm = PaymentMethod.query.get_or_404(pm_id)
    if pm.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Detach from Stripe
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        stripe.PaymentMethod.detach(pm.stripe_payment_method_id)
    except stripe.error.StripeError:
        pass  # Continue even if detachment fails

    db.session.delete(pm)
    db.session.commit()
    return jsonify({'success': True})


# ============ ORDER HISTORY ============
@bp.route('/orders')
@login_required
def order_history():
    """Display logged-in user's order history."""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('auth/orders.html', orders=orders)


@bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Display details of a specific order."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.order_history'))
    return render_template('auth/order_detail.html', order=order)


# In app/routes/auth.py, add after existing routes

@bp.route('/notifications')
@login_required
def notifications():
    """Show all user notifications."""
    page = request.args.get('page', 1, type=int)
    pagination = Notification.query.filter_by(user_id=current_user.id)\
                                   .order_by(Notification.created_at.desc())\
                                   .paginate(page=page, per_page=20)
    return render_template('auth/notifications.html', pagination=pagination)

@bp.route('/notification/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark a notification as read (AJAX)."""
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all user notifications as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        flash('Your email is already verified.', 'info')
    else:
        try:
            from app.services.email import send_verification_email
            send_verification_email(current_user)
            flash('Verification email sent. Please check your inbox.', 'success')
        except Exception as e:
            import traceback
            print("=== EMAIL ERROR ===")
            traceback.print_exc()
            current_app.logger.error(f"Resend verification error: {e}")
            flash('Could not send verification email. Please try again later.', 'danger')
    return redirect(url_for('auth.profile'))