from flask import Blueprint, render_template, request, jsonify, session, current_app, abort, make_response
from db import db, User, DashboardLayout, StockLevel, Transfer, Product, SalesOrder
from functools import wraps
from jsonschema import validate, ValidationError
import json
import os
import secrets
import logic

# blueprint
dashboard_bp = Blueprint("dashboard", __name__)

# Load JSON schema
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "../docs/schemas/dashboard_layout.schema.json")
if not os.path.exists(SCHEMA_PATH):
    # allow top-level docs path in repo root if blueprint is run from root
    SCHEMA_PATH = os.path.join(os.getcwd(), "docs", "schemas", "dashboard_layout.schema.json")
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    LAYOUT_SCHEMA = json.load(f)


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            abort(401)
        return f(*args, **kwargs)
    return wrapped


def require_manager(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("role") != "manager":
            return jsonify({"error": "forbidden"}), 403
        return f(*args, **kwargs)
    return wrapped


def require_csrf(f):
    """Double-submit cookie CSRF validator for JSON API endpoints."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Only enforce for state-changing JSON requests
        if request.method in ("POST", "PUT", "DELETE"):
            token_header = request.headers.get("X-CSRF-Token")
            token_cookie = request.cookies.get("csrf_token")
            if not token_header or not token_cookie or token_header != token_cookie:
                return jsonify({"error": "invalid_csrf"}), 403
        return f(*args, **kwargs)
    return wrapped


@dashboard_bp.route("/app/dashboard")
@login_required
def view_dashboard():
    user_id = session.get("user_id")
    role = session.get("role", "user")
    layout = DashboardLayout.query.filter_by(user_id=user_id).order_by(DashboardLayout.updated_at.desc()).first()
    if not layout:
        # fallback to role-default
        layout = DashboardLayout.query.filter_by(role=role).order_by(DashboardLayout.updated_at.desc()).first()

    layout_json = layout.layout_json if layout else {"panels": [{"id": "kpi_strip", "position": {"x":0,"y":0,"w":12,"h":1}}]}

    # ensure a fresh csrf token cookie is set for JS clients
    token = secrets.token_urlsafe(32)
    resp = make_response(render_template("dashboard.html", layout_json=layout_json))
    resp.set_cookie("csrf_token", token, httponly=False, samesite=current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax"))
    return resp

#
# API endpoints
#

@dashboard_bp.route("/api/csrf-token", methods=["GET"])
@login_required
def api_csrf_token():
    token = secrets.token_urlsafe(32)
    resp = jsonify({"csrf_token": token})
    resp.set_cookie("csrf_token", token, httponly=False, samesite=current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax"))
    return resp


@dashboard_bp.route("/api/dashboard/layouts/current", methods=["GET"])
@login_required
def api_get_current_layout():
    user_id = session.get("user_id")
    role = session.get("role", "user")
    layout = DashboardLayout.query.filter_by(user_id=user_id).order_by(DashboardLayout.updated_at.desc()).first()
    if not layout:
        layout = DashboardLayout.query.filter_by(role=role).order_by(DashboardLayout.updated_at.desc()).first()
    if not layout:
        return jsonify({"id": None, "layout_json": None, "version": None}), 404
    return jsonify({
        "id": layout.id,
        "user_id": layout.user_id,
        "role": layout.role,
        "layout_json": layout.layout_json,
        "version": layout.version,
        "updated_at": layout.updated_at.isoformat() if layout.updated_at else None
    })


@dashboard_bp.route("/api/dashboard/layouts", methods=["POST"])
@login_required
@require_csrf
def api_create_layout():
    user_id = session.get("user_id")
    payload = request.get_json()
    if not payload or "layout_json" not in payload:
        return jsonify({"error": "missing_payload"}), 400
    layout_json = payload["layout_json"]

    # validate against schema
    try:
        validate(instance=layout_json, schema=LAYOUT_SCHEMA)
    except ValidationError as e:
        return jsonify({"error": "invalid_layout", "message": str(e)}), 400

    new_layout = DashboardLayout(user_id=user_id, layout_json=layout_json, version=1)
    db.session.add(new_layout)
    db.session.commit()
    return jsonify({"id": new_layout.id, "version": new_layout.version}), 201


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["PUT"])
@login_required
@require_csrf
def api_update_layout(layout_id):
    user_id = session.get("user_id")
    payload = request.get_json()
    if not payload or "layout_json" not in payload or "version" not in payload:
        return jsonify({"error": "missing_payload"}), 400

    layout_json = payload["layout_json"]
    client_version = payload["version"]

    # validate JSON
    try:
        validate(instance=layout_json, schema=LAYOUT_SCHEMA)
    except ValidationError as e:
        return jsonify({"error": "invalid_layout", "message": str(e)}), 400

    layout = DashboardLayout.query.get(layout_id)
    if not layout:
        return jsonify({"error": "not_found"}), 404

    # ownership check: allow if user's layout or role-default update by manager
    if layout.user_id is not None and layout.user_id != user_id:
        return jsonify({"error": "forbidden"}), 403
    if layout.user_id is None:
        # role-default: only manager allowed to update
        if session.get("role") != "manager":
            return jsonify({"error": "forbidden_role_default"}), 403

    # optimistic locking
    if layout.version != client_version:
        return jsonify({
            "error": "stale",
            "message": "layout has changed",
            "current_version": layout.version,
            "current_layout": layout.layout_json
        }), 409

    # commit new layout
    layout.layout_json = layout_json
    layout.version = layout.version + 1
    db.session.add(layout)
    db.session.commit()
    return jsonify({"id": layout.id, "version": layout.version}), 200


@dashboard_bp.route("/api/dashboard/layouts/role-defaults", methods=["GET"])
@login_required
@require_manager
def api_get_role_defaults():
    layouts = DashboardLayout.query.filter(DashboardLayout.user_id == None).all()
    return jsonify([l.to_dict() for l in layouts])


@dashboard_bp.route("/api/dashboard/layouts/role-defaults", methods=["POST"])
@login_required
@require_manager
@require_csrf
def api_create_role_default():
    payload = request.get_json()
    if not payload or "layout_json" not in payload or "role" not in payload:
        return jsonify({"error": "missing_payload"}), 400
    layout_json = payload["layout_json"]
    role = payload["role"]

    try:
        validate(instance=layout_json, schema=LAYOUT_SCHEMA)
    except ValidationError as e:
        return jsonify({"error": "invalid_layout", "message": str(e)}), 400

    new_layout = DashboardLayout(user_id=None, role=role, layout_json=layout_json, version=1)
    db.session.add(new_layout)
    db.session.commit()
    return jsonify({"id": new_layout.id, "version": new_layout.version}), 201


@dashboard_bp.route("/api/panels/<panel_id>", methods=["GET"])
@login_required
def api_panel(panel_id):
    # Build stock list from DB
    stock_rows = StockLevel.query.all()
    stock = []
    for s in stock_rows:
        prod = Product.query.get(s.product_id)
        stock.append({
            "sku": prod.sku if prod else None,
            "product": prod.name if prod else None,
            "qty": s.qty,
            "min_qty": s.min_qty
        })

    transfers_rows = Transfer.query.all()
    transfers = []
    for t in transfers_rows:
        transfers.append({
            "ref": t.ref,
            "product_id": t.product_id,
            "qty": t.qty,
            "due": t.due_date.strftime("%Y-%m-%d") if t.due_date else None,
            "state": t.state
        })

    if panel_id == "kpi_strip":
        payload = logic.compute_stats(stock, transfers)
    elif panel_id == "stock_alerts":
        alerts = logic.get_alerts(stock)
        payload = {"alerts": alerts}
    elif panel_id == "transfers":
        payload = {"transfers": transfers}
    elif panel_id == "recent_activity":
        # use SalesOrder as recent activity
        orders = SalesOrder.query.order_by(SalesOrder.order_date.desc()).limit(10).all()
        payload = {"orders": [o.to_dict() for o in orders]}
    else:
        payload = {"message": f"panel {panel_id} not implemented yet"}

    return jsonify(payload)
