"""
Seed script for local development.

Creates:
- sqlite dev.db (via SQLAlchemy create_all)
- admin user (admin@example.com / passw0rd)
- sample products and stock levels
- sample sales orders and transfers
- sample team members
- role-default layouts for 'user' and 'manager'
"""
from db import db, User, Product, StockLevel, Transfer, SalesOrder, TeamMember, DashboardLayout
from app import create_app
from werkzeug.security import generate_password_hash
import json
from datetime import datetime, timedelta

app = create_app()
app.app_context().push()

db.create_all()

# Create admin user if not exists
admin_email = "admin@example.com"
admin = User.query.filter_by(email=admin_email).first()
if not admin:
    admin = User(email=admin_email, password_hash=generate_password_hash("passw0rd"), role="manager")
    db.session.add(admin)
    db.session.commit()
    print("✓ Created admin:", admin_email, "password: passw0rd")
else:
    print("✓ Admin exists:", admin_email)

# Create sample products
products_data = [
    {"sku": "PROD-001", "name": "Laptop Pro"},
    {"sku": "PROD-002", "name": "Wireless Mouse"},
    {"sku": "PROD-003", "name": "USB-C Cable"},
    {"sku": "PROD-004", "name": "Monitor 27\""},
    {"sku": "PROD-005", "name": "Keyboard Mechanical"}
]

products = {}
for prod_data in products_data:
    prod = Product.query.filter_by(sku=prod_data["sku"]).first()
    if not prod:
        prod = Product(sku=prod_data["sku"], name=prod_data["name"])
        db.session.add(prod)
    products[prod_data["sku"]] = prod

db.session.commit()
print(f"✓ Created/verified {len(products)} products")

# Create sample stock levels
for sku, prod in products.items():
    stock = StockLevel.query.filter_by(product_id=prod.id).first()
    if not stock:
        stock = StockLevel(product_id=prod.id, location="Warehouse-A", qty=50, min_qty=10)
        db.session.add(stock)

db.session.commit()
print("✓ Created sample stock levels")

# Create sample transfers
transfer_data = [
    {"ref": "TRF-001", "sku": "PROD-001", "qty": 10, "state": "pending"},
    {"ref": "TRF-002", "sku": "PROD-002", "qty": 25, "state": "in_transit"},
    {"ref": "TRF-003", "sku": "PROD-003", "qty": 100, "state": "delivered"}
]

for trans_data in transfer_data:
    trans = Transfer.query.filter_by(ref=trans_data["ref"]).first()
    if not trans:
        prod = products[trans_data["sku"]]
        trans = Transfer(
            ref=trans_data["ref"],
            product_id=prod.id,
            qty=trans_data["qty"],
            state=trans_data["state"],
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(trans)

db.session.commit()
print("✓ Created sample transfers")

# Create sample sales orders
sales_data = [
    {"ref": "SO-001", "customer": "Acme Corp", "amount": 5000.00, "status": "confirmed", "items": [{"sku": "PROD-001", "qty": 2}]},
    {"ref": "SO-002", "customer": "Tech Startup Inc", "amount": 1200.00, "status": "pending", "items": [{"sku": "PROD-002", "qty": 5}, {"sku": "PROD-003", "qty": 10}]},
    {"ref": "SO-003", "customer": "Global Enterprises", "amount": 12000.00, "status": "shipped", "items": [{"sku": "PROD-004", "qty": 3}]}
]

for sale_data in sales_data:
    sale = SalesOrder.query.filter_by(ref=sale_data["ref"]).first()
    if not sale:
        sale = SalesOrder(
            ref=sale_data["ref"],
            customer=sale_data["customer"],
            amount=sale_data["amount"],
            status=sale_data["status"],
            items_json=sale_data["items"]
        )
        db.session.add(sale)

db.session.commit()
print("✓ Created sample sales orders")

# Create sample team members
team_data = [
    {"name": "Alice Johnson", "email": "alice@example.com", "department": "Operations", "role": "Manager"},
    {"name": "Bob Smith", "email": "bob@example.com", "department": "Warehouse", "role": "Team Lead"},
    {"name": "Carol Davis", "email": "carol@example.com", "department": "Sales", "role": "Sales Rep"}
]

for member_data in team_data:
    member = TeamMember.query.filter_by(email=member_data["email"]).first()
    if not member:
        member = TeamMember(
            name=member_data["name"],
            email=member_data["email"],
            department=member_data["department"],
            role=member_data["role"]
        )
        db.session.add(member)

db.session.commit()
print("✓ Created sample team members")

# Create role-default layouts
# User layout
user_layout = DashboardLayout.query.filter_by(role="user").first()
if not user_layout:
    sample_layout_user = {
        "panels": [
            {"id": "kpi_strip", "position": {"x": 0, "y": 0, "w": 12, "h": 1}},
            {"id": "stock_alerts", "position": {"x": 0, "y": 1, "w": 6, "h": 6}},
            {"id": "transfers", "position": {"x": 6, "y": 1, "w": 6, "h": 6}}
        ]
    }
    user_layout = DashboardLayout(user_id=None, role="user", layout_json=sample_layout_user, version=1)
    db.session.add(user_layout)
    db.session.commit()
    print("✓ Created role-default user layout")
else:
    print("✓ Role-default user layout exists")

# Manager layout
manager_layout = DashboardLayout.query.filter_by(role="manager").first()
if not manager_layout:
    sample_layout_manager = {
        "panels": [
            {"id": "kpi_strip", "position": {"x": 0, "y": 0, "w": 12, "h": 1}},
            {"id": "stock_alerts", "position": {"x": 0, "y": 1, "w": 4, "h": 5}},
            {"id": "transfers", "position": {"x": 4, "y": 1, "w": 4, "h": 5}},
            {"id": "sales_summary", "position": {"x": 8, "y": 1, "w": 4, "h": 5}},
            {"id": "team_status", "position": {"x": 0, "y": 6, "w": 12, "h": 3}}
        ]
    }
    manager_layout = DashboardLayout(user_id=None, role="manager", layout_json=sample_layout_manager, version=1)
    db.session.add(manager_layout)
    db.session.commit()
    print("✓ Created role-default manager layout")
else:
    print("✓ Role-default manager layout exists")

print("\n✓ Seeding complete!")
