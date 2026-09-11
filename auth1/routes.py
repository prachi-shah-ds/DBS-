from flask import Blueprint, request, render_template, redirect, url_for, session, current_app, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db import db, User

auth_bp = Blueprint("auth_bp", __name__, template_folder="templates", static_folder="static")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    data = request.form or request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return render_template("login.html", error="Missing credentials"), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Invalid credentials"), 401
    # login
    session["user_id"] = user.id
    session["user_role"] = user.role
    current_app.logger.info("user_login", extra={"user_id": user.id})
    # respond depending on Accept
    if request.is_json:
        return jsonify({"message": "ok", "user": user.to_dict()})
    return redirect(url_for("dashboard_bp.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_role", None)
    return redirect(url_for("auth_bp.login"))


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)
