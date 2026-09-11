import pytest
from app import create_app
from app.db import db, User, DashboardLayout

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        # create test user
        u = User(email="u@example.com", password_hash="x", role="user")
        db.session.add(u); db.session.commit()
    yield app

def test_create_layout(client, app):
    # client fixture from pytest-flask or manual: use app.test_client
    cl = app.test_client()
    # set session manually (use flask.session interface or login endpoint)
    # For brevity, assume login endpoint exists and returns redirect
    res = cl.post("/login", data={"email": "admin@example.com", "password":"passw0rd"})
    # create layout
    res = cl.post("/api/dashboard/layouts", json={"layout_json":{"panels":[{"id":"kpi_strip","position":{"x":0,"y":0,"w":12,"h":1}}]}})
    assert res.status_code in (200,201)
