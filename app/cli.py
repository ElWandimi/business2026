import click
from flask import current_app, url_for
from flask.cli import with_appcontext
from datetime import datetime, timedelta
from flask import render_template

@click.command('send-abandoned-cart-emails')
@with_appcontext
def send_abandoned_cart_emails():
    """Send reminders for abandoned carts."""
    from app import db
    from app.models.cart import Cart
    from app.models.abandoned_cart import AbandonedCart
    from app.models.notification import Notification
    from app.services.email import send_email

    def send_abandoned_cart_email(cart, abandoned, first=True):
        """Helper to send the actual email and create a notification."""
        user = cart.user
        cart_items = cart.items.all()
        if not cart_items:
            return

        cart_url = url_for('cart.view_cart', _external=True)
        unsubscribe_url = url_for('main.unsubscribe_abandoned', token=user.generate_unsubscribe_token() if user else None, _external=True)

        if first:
            subject = "You left something in your cart!"
            template_html = 'email/abandoned_cart_first.html'
            template_txt = 'email/abandoned_cart_first.txt'
            abandoned.first_sent_at = datetime.utcnow()
        else:
            subject = "Still thinking about it? Your cart is waiting!"
            template_html = 'email/abandoned_cart_second.html'
            template_txt = 'email/abandoned_cart_second.txt'
            abandoned.second_sent_at = datetime.utcnow()

        html_body = render_template(template_html,
                                    user=user,
                                    cart_items=cart_items,
                                    cart_url=cart_url,
                                    unsubscribe_url=unsubscribe_url,
                                    site_name='WandimiMart')
        text_body = render_template(template_txt,
                                    user=user,
                                    cart_items=cart_items,
                                    cart_url=cart_url,
                                    unsubscribe_url=unsubscribe_url,
                                    site_name='WandimiMart')

        if user and not user.email_abandoned_cart_opt_out:
            send_email(user.email, subject, text_body, html_body)

            notif = Notification(
                user_id=user.id,
                type='abandoned_cart',
                title=subject,
                message='You have items waiting in your cart. Complete your purchase now!',
                link=url_for('cart.view_cart')
            )
            db.session.add(notif)
            db.session.commit()
        elif not user:
            pass

    # Configuration
    first_reminder_hours = 1
    second_reminder_hours = 24
    discount_code = 'COMEBACK10'  # optional, you could generate dynamically

    now = datetime.utcnow()

    # First reminders
    idle_threshold = now - timedelta(hours=first_reminder_hours)
    carts_to_remind = Cart.query.filter(
        Cart.updated_at <= idle_threshold,
        Cart.items.any(),
        ~Cart.abandoned_record.any()
    ).all()

    for cart in carts_to_remind:
        abandoned = AbandonedCart(
            cart_id=cart.id,
            user_id=cart.user_id,
            session_id=cart.session_id
        )
        db.session.add(abandoned)
        db.session.commit()
        send_abandoned_cart_email(cart, abandoned, first=True)

    # Second reminders
    second_threshold = now - timedelta(hours=second_reminder_hours)
    carts_to_remind_second = AbandonedCart.query.filter(
        AbandonedCart.first_sent_at <= second_threshold,
        AbandonedCart.second_sent_at == None,
        AbandonedCart.recovered_at == None
    ).all()

    for abandoned in carts_to_remind_second:
        cart = abandoned.cart
        if cart and cart.items.count() > 0:
            send_abandoned_cart_email(cart, abandoned, first=False)
        else:
            db.session.delete(abandoned)
            db.session.commit()


@click.command('seed-roles-permissions')
@with_appcontext
def seed_roles_permissions():
    """Seed default roles and permissions."""
    from app import db
    from app.models.role import Role, Permission

    # Define permissions
    permissions_data = [
        ('dashboard_access', 'dashboard_access', 'Access admin dashboard'),
        ('product_management', 'product_management', 'Manage products (create, edit, delete)'),
        ('order_management', 'order_management', 'Manage orders (view, update status)'),
        ('user_management', 'user_management', 'Manage customers (view, activate, deactivate)'),
        ('category_management', 'category_management', 'Manage product categories'),
        ('coupon_management', 'coupon_management', 'Manage coupons and promotions'),
        ('report_access', 'report_access', 'View analytics and reports'),
        ('support_management', 'support_management', 'Manage support conversations'),
        ('inventory_management', 'inventory_management', 'Manage inventory (stock levels)'),
        ('gift_card_management', 'gift_card_management', 'Manage gift cards'),
        ('role_management', 'role_management', 'Manage admin roles and permissions (Super Admin only)'),
    ]

    for name, codename, desc in permissions_data:
        perm = Permission.query.filter_by(codename=codename).first()
        if not perm:
            perm = Permission(name=name, codename=codename, description=desc)
            db.session.add(perm)
    db.session.commit()

    # Define roles
    roles_data = [
        ('Super Admin', 'Full system access', []),
        ('Admin', 'Standard admin with most permissions', [
            'dashboard_access', 'product_management', 'order_management',
            'user_management', 'category_management', 'coupon_management',
            'report_access', 'support_management', 'inventory_management'
        ]),
        ('Content Manager', 'Manage products and content', [
            'product_management', 'category_management'
        ]),
        ('Order Manager', 'Handle orders only', [
            'order_management'
        ]),
    ]

    for role_name, role_desc, perm_codenames in roles_data:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=role_desc)
            db.session.add(role)
            db.session.flush()
            for codename in perm_codenames:
                perm = Permission.query.filter_by(codename=codename).first()
                if perm:
                    role.permissions.append(perm)
    db.session.commit()
    print("Roles and permissions seeded.")