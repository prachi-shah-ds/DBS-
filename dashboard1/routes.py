import json
from flask import Blueprint, request, render_template, jsonify, abort, session, current_app, make_response
from jsonschema import validate, ValidationError
from db import db, DashboardLayout, User, StockLevel, Transfer, SalesOrder, AuditLog
from logic import compute_stats, get_alerts, get_status  # existing logic.py in repo
from functools import wraps
import secrets
import os


dashboard_bp = Blueprint("dashboard_bp", __name__, template_folder="templates", static_folder="static")


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            abort(401)
        return f(*args, **kwargs)
    return wrapped


def require_csrf(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.method in ("POST", "PUT", "DELETE"):
            token_header = request.headers.get("X-CSRF-Token")
            token_cookie = request.cookies.get("csrf_token")
            if not token_header or not token_cookie or token_header != token_cookie:
                return jsonify({"error": "invalid_csrf"}), 403
        return f(*args, **kwargs)
    return wrapped


def get_current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


# Serve dashboard page (server-rendered shell)
@dashboard_bp.route("/app/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    layout = None
    if user:
        layout = DashboardLayout.query.filter_by(user_id=user.id).order_by(DashboardLayout.updated_at.desc()).first()
    if not layout:
        # fallback to role-default using session key 'role'
        role = session.get("role", "user")
        layout = DashboardLayout.query.filter_by(role=role).order_by(DashboardLayout.updated_at.desc()).first()

    layout_data = layout.layout_json if layout else {"panels": []}
    # set CSRF token cookie for JS clients (double-submit pattern)
    token = secrets.token_urlsafe(32)
    resp = make_response(render_template("dashboard.html", layout_json=layout_data, layout_id=(layout.id if layout else None)))
    resp.set_cookie("csrf_token", token, httponly=False, samesite=current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax"))
    return resp


# CRUD API for dashboard layouts
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "../docs/schemas/dashboard_layout.schema.json")
if not os.path.exists(SCHEMA_PATH):
    SCHEMA_PATH = os.path.join(os.getcwd(), "docs", "schemas", "dashboard_layout.schema.json")
try:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        LAYOUT_SCHEMA = json.load(f)
except Exception:
    LAYOUT_SCHEMA = None


@dashboard_bp.route("/api/dashboard/layouts/current", methods=["GET"])
@login_required
def api_get_current_layout():
    user = get_current_user()
    if not user:
        return jsonify({"id": None, "layout_json": None, "version": None}), 404
    layout = DashboardLayout.query.filter_by(user_id=user.id).order_by(DashboardLayout.updated_at.desc()).first()
    if not layout:
        role = session.get("role", "user")
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


@dashboard_bp.route("/api/dashboard/layouts", methods=["GET"])
@login_required
def list_layouts():
    user = get_current_user()
    if not user:
        return jsonify([]), 200
    layouts = DashboardLayout.query.filter_by(user_id=user.id).all()
    return jsonify([l.to_dict() for l in layouts])


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["GET"])
@login_required
def get_layout(layout_id):
    user = get_current_user()
    layout = DashboardLayout.query.get_or_404(layout_id)
    # ownership: allow if owner or role-default (user_id is null and matches role)
    if layout.user_id and (not user or layout.user_id != user.id):
        return abort(403)
    return jsonify(layout.to_dict())


@dashboard_bp.route("/api/dashboard/layouts", methods=["POST"])
@login_required
@require_csrf
def create_layout():
    user = get_current_user()
    if not user:
        return abort(401)
    body = request.get_json() or {}
    # accept either { "layout_json": {...} } or the layout object directly
    layout_json = body.get("layout_json") if isinstance(body, dict) and "layout_json" in body else body
    if LAYOUT_SCHEMA:
        try:
            validate(instance=layout_json, schema=LAYOUT_SCHEMA)
        except ValidationError as e:
            return jsonify({"error": "invalid_schema", "detail": str(e)}), 400
    layout = DashboardLayout(user_id=user.id, role=None, layout_json=layout_json, version=1)
    db.session.add(layout)
    db.session.commit()
    # audit log
    try:
        audit = AuditLog(user_id=user.id, action="layout.create", target=f"layout:{layout.id}", details=json.dumps({"role": layout.role}))
        db.session.add(audit)
        db.session.commit()
    except Exception:
        current_app.logger.exception("audit log failed")
    current_app.logger.info("layout.create", extra={"user_id": user.id, "layout_id": layout.id})
    return jsonify(layout.to_dict()), 201


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["PUT"])
@login_required
@require_csrf
def update_layout(layout_id):
    user = get_current_user()
    if not user:
        return abort(401)
    layout = DashboardLayout.query.get_or_404(layout_id)
    if layout.user_id and layout.user_id != user.id:
        return abort(403)
    body = request.get_json() or {}
    # accept wrapper or body with panels
    layout_json = body.get("layout_json") if isinstance(body, dict) and "layout_json" in body else body.get("panels") if isinstance(body, dict) and "panels" in body else body
    client_version = body.get("version") if isinstance(body, dict) else None
    if LAYOUT_SCHEMA:
        try:
            validate(instance=layout_json, schema=LAYOUT_SCHEMA)
        except ValidationError as e:
            return jsonify({"error": "invalid_schema", "detail": str(e)}), 400
    if client_version is None:
        return jsonify({"error": "missing_version"}), 400
    if client_version != layout.version:
        return jsonify({"error": "version_conflict", "current_version": layout.version}), 409
    layout.layout_json = layout_json
    layout.version = layout.version + 1
    db.session.commit()
    # audit
    try:
        audit = AuditLog(user_id=user.id, action="layout.update", target=f"layout:{layout.id}", details=json.dumps({"version": layout.version}))
        db.session.add(audit)
        db.session.commit()
    except Exception:
        current_app.logger.exception("audit log failed")
    current_app.logger.info("layout.update", extra={"user_id": user.id, "layout_id": layout.id, "version": layout.version})
    return jsonify(layout.to_dict()), 200


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["DELETE"])
@login_required
@require_csrf
def delete_layout(layout_id):
    user = get_current_user()
    if not user:
        return abort(401)
    layout = DashboardLayout.query.get_or_404(layout_id)
    if layout.user_id and layout.user_id != user.id:
        return abort(403)
    db.session.delete(layout)
    db.session.commit()
    try:
        audit = AuditLog(user_id=user.id, action="layout.delete", target=f"layout:{layout_id}", details=None)
        db.session.add(audit)
        db.session.commit()
    except Exception:
        current_app.logger.exception("audit log failed")
    current_app.logger.info("layout.delete", extra={"user_id": user.id, "layout_id": layout_id})
    return "", 204


# Panel data endpoint (simple mocked outputs using logic functions)
@dashboard_bp.route("/api/panels/<panel_id>")
@login_required
def panel_data(panel_id):
    # Query params can include range etc.
    if panel_id == "kpi_strip":
        # compute summaries using existing compute_stats if available
        stock = [s.to_dict() for s in StockLevel.query.all()]
        transfers = [t.to_dict() for t in Transfer.query.all()]
        stats = compute_stats(stock, transfers) if compute_stats else {"total_skus": len(stock)}
        return jsonify({"panel": "kpi_strip", "data": stats})
    if panel_id == "stock_alerts":
        stock = [s.to_dict() for s in StockLevel.query.all()]
        alerts = get_alerts(stock) if get_alerts else []
        return jsonify({"panel": "stock_alerts", "data": alerts})
    if panel_id == "transfers":
        transfers = [t.to_dict() for t in Transfer.query.all()]
        return jsonify({"panel": "transfers", "data": transfers})
    if panel_id == "sales_summary":
        orders = [o.to_dict() for o in SalesOrder.query.all()]
        return jsonify({"panel": "sales_summary", "data": orders})
    # fallback
    return jsonify({"panel": panel_id, "data": {}}), 200
