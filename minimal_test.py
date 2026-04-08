from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from pathlib import Path

# Create absolute path
basedir = Path(__file__).parent.absolute()
db_path = basedir / 'instance' / 'minimal.db'
db_uri = f'sqlite:///{db_path}'

print(f"Attempting to create database at: {db_path}")
print(f"Database URI: {db_uri}")

# Test if we can write to the directory
test_file = basedir / 'instance' / 'write_test.txt'
try:
    test_file.write_text('test')
    print(f"✅ Can write to instance directory: {test_file}")
    test_file.unlink()
except Exception as e:
    print(f"❌ Cannot write to instance directory: {e}")

# Create minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)

try:
    with app.app_context():
        db.create_all()
        print("✅ Database created successfully!")
        print(f"Database file exists: {db_path.exists()}")
        print(f"Database file size: {db_path.stat().st_size if db_path.exists() else 0} bytes")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nChecking file permissions:")
print(f"Instance directory permissions: {oct(os.stat(basedir / 'instance').st_mode)[-3:]}")
print(f"Parent directory permissions: {oct(os.stat(basedir).st_mode)[-3:]}")
