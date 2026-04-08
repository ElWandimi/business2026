import sys
import os
from pathlib import Path

print("=== DEBUG INFORMATION ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

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
    
    # Print the database URI FIRST
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"\n🔍 Database URI: {db_uri}")
    
    # Extract and check the file path
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        print(f"📁 Database file path: {db_path}")
        print(f"📁 Database directory: {Path(db_path).parent}")
        print(f"📁 Directory exists: {Path(db_path).parent.exists()}")
        print(f"📁 Directory writable: {os.access(Path(db_path).parent, os.W_OK)}")
    
    # Now try to create tables
    print("\n=== CREATING TABLES ===")
    with app.app_context():
        from app import db
        db.create_all()
        print("✅ Successfully created database tables")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
