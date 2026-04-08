import sys
import os
from pathlib import Path

print("=== DEBUG INFORMATION ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {__file__}")

# Check if config.py exists and can be read
config_path = Path("config.py")
print(f"config.py exists: {config_path.exists()}")
if config_path.exists():
    print(f"config.py readable: {os.access(config_path, os.R_OK)}")

# Check instance directory
instance_dir = Path("instance")
print(f"Instance directory absolute path: {instance_dir.absolute()}")
print(f"Instance directory exists: {instance_dir.exists()}")
print(f"Instance directory writable: {os.access(instance_dir, os.W_OK)}")

# Try to create a test file in instance directory
test_file = instance_dir / "flask_test.txt"
try:
    test_file.write_text("test")
    print(f"✅ Successfully wrote test file to instance directory")
    test_file.unlink()
except Exception as e:
    print(f"❌ Failed to write to instance directory: {e}")

print("\n=== LOADING APP ===")
try:
    from app import create_app
    print("✅ Successfully imported create_app")
    
    app = create_app()
    print("✅ Successfully created app")
    
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Extract the file path from the URI
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        print(f"Database file path: {db_path}")
        print(f"Database directory exists: {Path(db_path).parent.exists()}")
        print(f"Can write to database directory: {os.access(Path(db_path).parent, os.W_OK)}")
    
    # Try to create tables
    with app.app_context():
        from app import db
        db.create_all()
        print("✅ Successfully created database tables")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
