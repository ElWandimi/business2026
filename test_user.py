from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    # Create tables
    db.create_all()
    
    # Test user creation
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Test password verification
    test_user = User.query.filter_by(username='testuser').first()
    print(f"User created: {test_user.username}")
    print(f"Password check (should be True): {test_user.check_password('password123')}")
    print(f"Password check (should be False): {test_user.check_password('wrongpassword')}")
    
    # Clean up
    db.session.delete(test_user)
    db.session.commit()
    print("Test completed and cleaned up")
