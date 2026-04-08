# app/services/email.py
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from flask import render_template
from flask import url_for, render_template

logger = logging.getLogger(__name__)

def send_email(recipient, subject, body, html_body=None):
    """
    Send an email using the configured SMTP server.
    """
    try:
        mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_use_tls = current_app.config.get('MAIL_USE_TLS', True)
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)

        if not mail_username or not mail_password:
            logger.error("Mail credentials not configured")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(mail_server, mail_port) as server:
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)

        logger.info(f"Email sent to {recipient}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False

# ========== Order emails ==========
def send_order_confirmation(order):
    subject = f"Order Confirmation #{order.order_number}"
    body = f"""
    Dear {order.shipping_first_name or 'Customer'},

    Thank you for your order! Your order #{order.order_number} has been received and is being processed.

    Order total: ${order.total:.2f}

    We will notify you when your order ships.

    Best regards,
    Business2026 Team
    """
    send_email(order.user.email if order.user else order.shipping_email, subject, body)

def send_order_status_update(order):
    subject = f"Order #{order.order_number} Status Update"
    body = f"""
    Dear {order.shipping_first_name or 'Customer'},

    Your order #{order.order_number} status has been updated to: {order.status}.

    """
    if order.tracking_number:
        body += f"Tracking number: {order.tracking_number} via {order.carrier or 'carrier'}\n"
        body += "You can track your package on the carrier's website.\n"

    body += """
    Thank you for shopping with Business2026!

    Best regards,
    Business2026 Team
    """
    send_email(order.user.email if order.user else order.shipping_email, subject, body)

# ========== Support emails ==========
def send_support_confirmation(conversation):
    subject = "Support Request Received - Business2026"
    body = f"""
Dear {conversation.name},

Thank you for contacting Business2026 Support.
Your request has been received and a support representative will get back to you shortly.

Your conversation reference: #{conversation.id}
Email: {conversation.email}
Order Number: {conversation.order_number or 'N/A'}

You will receive replies both here and directly in your chat window on our website.

Best regards,
Business2026 Support Team
    """
    send_email(conversation.email, subject, body)

def send_support_reply(conversation, message_text):
    subject = f"Support Reply #{conversation.id} - Business2026"
    body = f"""
Dear {conversation.name},

You have received a new reply from our support team:

--------------------
{message_text}
--------------------

You can continue the conversation in the chat widget on our website.

Best regards,
Business2026 Support Team
    """
    send_email(conversation.email, subject, body)

# ========== Authentication emails ==========
def send_verification_email(user):
    """Send email verification link."""
    token = user.generate_email_verification_token()
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    site_name = current_app.config.get('SITE_NAME', 'business2026')
    html_body = render_template('email/verify.html', user=user, verify_url=verify_url, site_name=site_name)
    send_email(user.email, f'Verify Your Email - {site_name}', 'Please verify your email.', html_body)

def send_welcome_email(user):
    """Send welcome email after registration."""
    site_name = current_app.config.get('SITE_NAME', 'business2026')
    site_url = current_app.config.get('SITE_URL', 'http://localhost:5001')
    html_body = render_template('email/welcome.html', user=user, site_name=site_name, site_url=site_url)
    send_email(user.email, f'Welcome to {site_name}!', 'Welcome to our store!', html_body)

def send_password_reset_email(user):
    """Send password reset link."""
    token = user.generate_reset_password_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    site_name = current_app.config.get('SITE_NAME', 'business2026')
    html_body = render_template('email/reset_password.html', user=user, reset_url=reset_url, site_name=site_name)
    send_email(user.email, f'Reset Your Password - {site_name}', 'Reset your password.', html_body)

# ========== Gift card email ==========
def send_gift_card_email(recipient_email, code, amount, sender_name):
    subject = f"You've received a WandimiMart Gift Card worth ${amount:.2f}!"
    text_body = f"Dear friend,\n\nYou have received a gift card worth ${amount:.2f} from {sender_name}.\n\nYour code: {code}\n\nYou can redeem it at checkout on WandimiMart.\n\nThank you!"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:20px;">
            <h2 style="color:#2E7D32;">You've received a gift card!</h2>
            <p>You have received a WandimiMart gift card worth <strong>${amount:.2f}</strong> from <strong>{sender_name}</strong>.</p>
            <p style="font-size:1.2rem; background:#f5f5f5; padding:10px; text-align:center;"><strong>{code}</strong></p>
            <p>To redeem, simply enter this code at checkout.</p>
            <p>Happy shopping!</p>
        </div>
    </body>
    </html>
    """
    send_email(recipient_email, subject, text_body, html_body)