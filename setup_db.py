from app import create_app, db
from app.models import Role, Permission
from app.cli import seed_roles_permissions
import sys

app = create_app()
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Tables created.")
    
    print("Seeding roles and permissions...")
    if Role.query.count() == 0:
        seed_roles_permissions()
    else:
        print("Roles already exist, skipping seed.")
    
    print("Database setup complete.")