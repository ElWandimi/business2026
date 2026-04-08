import random
import string
from flask import request
from app import db
from app.models.admin_log import AdminLog

def generate_coupon_code(length=8, prefix='', suffix=''):
    """Generate a random coupon code (uppercase letters + digits)."""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=length))
    if prefix:
        code = prefix + code
    if suffix:
        code = code + suffix
    return code

def log_admin_action(user_id, action, target, details):
    """Log an admin action (assumes we are inside a Flask request context)."""
    try:
        log = AdminLog(
            user_id=user_id,
            action=action,
            target=target,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Log error but don't break the main flow
        import logging
        logging.error(f"Failed to log admin action: {e}")