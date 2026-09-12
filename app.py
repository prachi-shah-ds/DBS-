from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Configuration
    app.config.from_object("config.Config")

    # Initialize extensions and register blueprints
    from db import db
    db.init_app(app)

    from flask_wtf import CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app)

    from auth.routes import auth_bp
    # use dashboard1 as requested
    from dashboard1.routes import dashboard_bp as dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    @app.route("/version")
    def version():
        return {"version": os.getenv("APP_VERSION", "0.0.0")}, 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
