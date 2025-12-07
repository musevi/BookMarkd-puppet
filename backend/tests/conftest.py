import os
import sys
from pathlib import Path
import pytest

# Add the backend directory to sys.path so we can import modules
TESTS_DIR = Path(__file__).resolve().parent  # tests/
BACKEND_DIR = TESTS_DIR.parent  # backend/

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from extensions import db
from models import User

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    # Use in-memory SQLite for tests (no real database needed!)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()  # Create tables
        yield app
        db.session.remove()
        db.drop_all()  # Clean up after tests

@pytest.fixture
def client(app):
    """Test client for making requests"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner for testing commands"""
    return app.test_cli_runner()

@pytest.fixture
def sample_user(app):
    """Create a sample user for testing and return user_id"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user.user_id
