from app import create_app, db
from app.models import Role, Permission
import os

app = create_app()

with app.app_context():
    # Run migrations (create tables if they don't exist)
    db.create_all()
    
    # Seed roles and permissions if they are empty
    if Role.query.count() == 0:
        from app.cli import seed_roles_permissions
        seed_roles_permissions()