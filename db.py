from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "role": self.role}


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "sku": self.sku, "name": self.name}


class StockLevel(db.Model):
    __tablename__ = "stock_level"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=0)
    min_qty = db.Column(db.Integer, nullable=False, default=10)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship("Product", backref="stock_levels")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "location": self.location,
            "qty": self.qty,
            "min_qty": self.min_qty,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Transfer(db.Model):
    __tablename__ = "transfer"
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String(100), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    state = db.Column(db.String(32), nullable=False, default="pending")  # pending, in_transit, delivered
    assigned_to = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product", backref="transfers")

    def to_dict(self):
        return {
            "id": self.id,
            "ref": self.ref,
            "product_id": self.product_id,
            "qty": self.qty,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "state": self.state,
            "assigned_to": self.assigned_to
        }


class SalesOrder(db.Model):
    __tablename__ = "sales_order"
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String(100), unique=True, nullable=False)
    customer = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending")  # pending, confirmed, shipped, delivered
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    items_json = db.Column(SQLITE_JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "ref": self.ref,
            "customer": self.customer,
            "amount": self.amount,
            "status": self.status,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "items": self.items_json
        }


class TeamMember(db.Model):
    __tablename__ = "team_member"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="active")  # active, inactive, on_leave
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "role": self.role,
            "status": self.status
        }


class DashboardLayout(db.Model):
    __tablename__ = "dashboard_layout"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # null => role-default
    role = db.Column(db.String(32), nullable=True)  # "manager" or "user" for role-default
    layout_json = db.Column(SQLITE_JSON, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="layouts")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "layout_json": self.layout_json,
            "version": self.version,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(128), nullable=False)
    target = db.Column(db.String(256), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "target": self.target,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
