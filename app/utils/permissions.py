from functools import wraps
from flask import flash, redirect, url_for, current_app
from flask_login import current_user

def permission_required(permission_codename):
    """Decorator to check if the current user has the given permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Super admin bypasses all checks
            if current_user.is_super_admin:
                return f(*args, **kwargs)
            # Check if user has the required permission
            if not current_user.is_authenticated:
                flash('Please log in.', 'danger')
                return redirect(url_for('auth.login'))
            # Check via roles/permissions
            user_perms = [p.codename for p in current_user.permissions]
            for role in current_user.roles:
                user_perms.extend([p.codename for p in role.permissions])
            if permission_codename in user_perms:
                return f(*args, **kwargs)
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return decorated_function
    return decorator