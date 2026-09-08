import pytest
from app import create_app
from db import db, User, Product, StockLevel, Transfer
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all()
            # seed user
            u = User(email="u2@example.com", password_hash=generate_password_hash("pw"), role="user")
            db.session.add(u)
            # seed product + stock + transfer
            p = Product(sku="SKU-100", name="Widget")
            db.session.add(p)
            db.session.commit()
            sl = StockLevel(product_id=p.id, location="WH1", qty=2, min_qty=10)
            db.session.add(sl)
            t = Transfer(ref="T-1", product_id=p.id, qty=5, state="draft")
            db.session.add(t)
            db.session.commit()
        yield client


def login(client):
    r = client.post("/login", json={"email":"u2@example.com","password":"pw"})
    assert r.status_code == 200


def test_panels_and_csrf(client):
    # login and fetch csrf
    login(client)
    r = client.get("/api/csrf-token")
    assert r.status_code == 200
    token = r.get_json().get("csrf_token")
    assert token

    # fetch kpi panel
    r2 = client.get("/api/panels/kpi_strip")
    assert r2.status_code == 200
    data = r2.get_json()
    assert "total_skus" in data

    # try creating layout without csrf header => forbidden
    payload = {"layout_json": {"panels": [{"id":"kpi_strip","position":{"x":0,"y":0,"w":12,"h":1}}]}}
    r3 = client.post("/api/dashboard/layouts", json=payload)
    assert r3.status_code == 403

    # with header should succeed
    r4 = client.post("/api/dashboard/layouts", json=payload, headers={"X-CSRF-Token": token})
    assert r4.status_code == 201
