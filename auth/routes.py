from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import db, User
from itsdangerous import URLSafeTimedSerializer
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login_post():
    # supports form-encoded or JSON payloads
    if request.is_json:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
    else:
        email = request.form.get("email")
        password = request.form.get("password")

    if not email or not password:
        return jsonify({"ok": False, "error": "missing_credentials"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401

    session.clear()
    session["user_id"] = user.id
    session["role"] = user.role

    # redirect or JSON
    if request.is_json:
        return jsonify({"ok": True, "redirect": url_for("dashboard.view_dashboard")})
    return redirect(url_for("dashboard.view_dashboard"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_get"))

# Password reset skeleton (dev mode: token printed to logs)

def _get_serializer():
    secret = current_app.config.get("SECRET_KEY") or os.getenv("SECRET_KEY")
    return URLSafeTimedSerializer(secret)

@auth_bp.route("/auth/request-password-reset", methods=["POST"])
def request_password_reset():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "missing_email"}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        # return 200 to avoid leaking existence
        current_app.logger.info("Password reset requested for unknown email: %s", email)
        return jsonify({"ok": True}), 200

    s = _get_serializer()
    token = s.dumps({"user_id": user.id})
    # In production, send token via email. For dev, we log it.
    current_app.logger.info("Password reset token for %s: %s", email, token)
    return jsonify({"ok": True, "note": "token_logged"}), 200

@auth_bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token = data.get("token")
    new_password = data.get("new_password")
    if not token or not new_password:
        return jsonify({"error": "missing_fields"}), 400

    s = _get_serializer()
    try:
        payload = s.loads(token, max_age=3600)
    except Exception as e:
        return jsonify({"error": "invalid_or_expired_token"}), 400

    user_id = payload.get("user_id")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    user.password_hash = generate_password_hash(new_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"ok": True}), 200
