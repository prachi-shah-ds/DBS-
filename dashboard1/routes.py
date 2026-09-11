import json
from flask import Blueprint, request, render_template, jsonify, abort, session, current_app
from jsonschema import validate, ValidationError
from db import db, DashboardLayout, User, StockLevel, Transfer, SalesOrder
from logic import compute_stats, get_alerts, get_status  # existing logic.py in repo

dashboard_bp = Blueprint("dashboard_bp", __name__, template_folder="templates", static_folder="static")


def get_current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


# Serve dashboard page (server-rendered shell)
@dashboard_bp.route("/app/dashboard")
def dashboard():
    user = get_current_user()
    # server can inline user's layout JSON for fast render
    layout = None
    if user:
        layout = DashboardLayout.query.filter_by(user_id=user.id).first()
    if not layout:
        # fallback to role-default layout
        role = session.get("user_role")
        layout = DashboardLayout.query.filter_by(role=role).first()
    layout_data = layout.layout_json if layout else {"panels": []}
    return render_template("dashboard.html", layout=layout_data, layout_id=(layout.id if layout else None))


# CRUD API for dashboard layouts
SCHEMA_PATH = "docs/schemas/dashboard_layout.schema.json"
try:
    with open(SCHEMA_PATH, "r") as f:
        DASHBOARD_SCHEMA = json.load(f)
except Exception:
    DASHBOARD_SCHEMA = None
    current_app.logger = current_app.logger if hasattr(current_app, "logger") else None


@dashboard_bp.route("/api/dashboard/layouts", methods=["GET"])
def list_layouts():
    user = get_current_user()
    if not user:
        return jsonify([]), 200
    layouts = DashboardLayout.query.filter_by(user_id=user.id).all()
    return jsonify([l.to_dict() for l in layouts])


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["GET"])
def get_layout(layout_id):
    user = get_current_user()
    layout = DashboardLayout.query.get_or_404(layout_id)
    # ownership: allow if owner or role-default (user_id is null and matches role)
    if layout.user_id and (not user or layout.user_id != user.id):
        return abort(403)
    return jsonify(layout.to_dict())


@dashboard_bp.route("/api/dashboard/layouts", methods=["POST"])
def create_layout():
    user = get_current_user()
    if not user:
        return abort(401)
    body = request.get_json() or {}
    # validate
    if DASHBOARD_SCHEMA:
        try:
            validate(instance=body, schema=DASHBOARD_SCHEMA)
        except ValidationError as e:
            return jsonify({"error": "invalid_schema", "detail": e.message}), 400
    layout = DashboardLayout(user_id=user.id, role=None, layout_json=body.get("panels", body), version=1)
    db.session.add(layout)
    db.session.commit()
    current_app.logger.info("layout.create", extra={"user_id": user.id, "layout_id": layout.id})
    return jsonify(layout.to_dict()), 201


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["PUT"])
def update_layout(layout_id):
    user = get_current_user()
    if not user:
        return abort(401)
    layout = DashboardLayout.query.get_or_404(layout_id)
    if layout.user_id and layout.user_id != user.id:
        return abort(403)
    body = request.get_json() or {}
    if DASHBOARD_SCHEMA:
        try:
            validate(instance=body, schema=DASHBOARD_SCHEMA)
        except ValidationError as e:
            return jsonify({"error": "invalid_schema", "detail": e.message}), 400
    # optimistic locking
    client_version = body.get("version")
    if client_version is None:
        return jsonify({"error": "missing_version"}), 400
    if client_version != layout.version:
        return jsonify({"error": "version_conflict", "current_version": layout.version}), 409
    layout.layout_json = body.get("panels", body)
    layout.version = layout.version + 1
    db.session.commit()
    current_app.logger.info("layout.update", extra={"user_id": user.id, "layout_id": layout.id, "version": layout.version})
    return jsonify(layout.to_dict()), 200


@dashboard_bp.route("/api/dashboard/layouts/<int:layout_id>", methods=["DELETE"])
def delete_layout(layout_id):
    user = get_current_user()
    if not user:
        return abort(401)
    layout = DashboardLayout.query.get_or_404(layout_id)
    if layout.user_id and layout.user_id != user.id:
        return abort(403)
    db.session.delete(layout)
    db.session.commit()
    current_app.logger.info("layout.delete", extra={"user_id": user.id, "layout_id": layout_id})
    return "", 204


# Panel data endpoint (simple mocked outputs using logic functions)
@dashboard_bp.route("/api/panels/<panel_id>")
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
