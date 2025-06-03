import pytest
import sys
from pathlib import Path
from flask import template_rendered
from contextlib import contextmanager


sys.path.insert(0, str(Path(__file__).parent.parent))

from app_web.sistema import create_app, pgdb

@pytest.fixture(scope='function')
def app():
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'  
    })

    # Initialize database
    with app.app_context():

        pgdb.init_app(app)
        yield app


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth(client):
    class AuthActions:
        def login(self, email='admin@example.com', password='password'):
            with client.session_transaction() as sess:
                sess['usuario_id'] = 1  
                sess['rol_id'] = 1     
            return client.get('/')  
            
        def logout(self):
            with client.session_transaction() as sess:
                sess.clear()
            return client.get('/')
    
    return AuthActions()

@contextmanager
def captured_templates(app):
    recorded = []
    
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)