import pytest
import sys
from pathlib import Path
from flask import template_rendered
from contextlib import contextmanager

# Add the main directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_web.sistema import create_app, pgdb

@pytest.fixture(scope='function')
def app():
    """Create and configure a new app instance for each test"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'  # Using SQLite in memory
    })

    # Initialize database
    with app.app_context():
        # If your pgdb has init_app method
        pgdb.init_app(app)
        
        # If you need to create tables, you might need to:
        # 1. Either use SQLAlchemy's create_all() if you're using it
        # 2. Or implement appropriate methods in your PostgresDB class
        # For now, we'll skip table creation since it's causing errors
        
        yield app

        # Cleanup if needed
        # pgdb.drop_all() if implemented

@pytest.fixture
def client(app):
    """Test client for making requests"""
    return app.test_client()

@pytest.fixture
def auth(client):
    """Fixture for handling authentication in tests"""
    class AuthActions:
        def login(self, email='admin@example.com', password='password'):
            with client.session_transaction() as sess:
                sess['usuario_id'] = 1  # Test user ID
                sess['rol_id'] = 1      # Admin role
            return client.get('/')  # Simulate login by redirecting to home
            
        def logout(self):
            with client.session_transaction() as sess:
                sess.clear()
            return client.get('/')
    
    return AuthActions()

# Remove the setup_db fixture for now since it's causing scope issues
# We'll handle DB setup in the app fixture

@contextmanager
def captured_templates(app):
    """Capture templates rendered during tests"""
    recorded = []
    
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)