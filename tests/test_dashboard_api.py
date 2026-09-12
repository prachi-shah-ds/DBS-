import json
from app import create_app
from db import db, User
import pytest

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        # create a test user
        user = User(email="test@example.com", password_hash="noop", role="user")
        db.session.add(user)
        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def login(client):
    # seed has admin@example.com but in test we create test@example.com; skip auth and set session via cookie not trivial here
    pass

def test_get_current_layout_empty(client, app):
    # without login should return 404
    res = client.get('/api/dashboard/layouts/current')
    assert res.status_code in (401, 404)
