from datetime import datetime, date
from flask import Flask, session
from app.config import Config
from app.api_client import api


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init API client base URL from config
    api._base_url = app.config["SERVER_BASE_URL"]

    # Jinja2 filter: format date from string or datetime object
    @app.template_filter("date_fmt")
    def date_fmt(value, fmt="%Y-%m-%d"):
        if value is None:
            return ""
        if isinstance(value, (datetime, date)):
            return value.strftime(fmt)
        # Parse ISO date string (handles both "2026-05-27" and "2026-05-27 10:42:28")
        try:
            val = value.strip()
            if " " in val:
                dt = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            elif "T" in val:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(val, "%Y-%m-%d")
            return dt.strftime(fmt)
        except (ValueError, AttributeError):
            return str(value)

    # Context processor: inject current_user from session for template compatibility
    @app.context_processor
    def inject_user():
        teacher = session.get("teacher")
        if teacher:
            return {
                "current_user": type("UserProxy", (), {
                    "is_authenticated": True,
                    "is_admin": teacher.get("is_admin", False),
                    "is_active": teacher.get("is_active", True),
                    "id": teacher.get("id"),
                    "username": teacher.get("username", ""),
                    "display_name": teacher.get("display_name", ""),
                })()
            }
        return {
            "current_user": type("AnonProxy", (), {
                "is_authenticated": False,
                "is_admin": False,
                "is_active": False,
                "id": None,
                "username": "",
                "display_name": "",
            })()
        }

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.courses import courses_bp
    from app.routes.students import students_bp
    from app.routes.templates import templates_bp
    from app.routes.send import send_bp
    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(send_bp)

    # Error handler for API connection failures
    @app.errorhandler(Exception)
    def handle_exception(e):
        import requests as _requests
        if isinstance(e, _requests.ConnectionError):
            return render_error("无法连接到服务器，请检查网络连接或服务器状态")
        if isinstance(e, _requests.Timeout):
            return render_error("服务器请求超时，请稍后重试")
        raise e

    return app


def render_error(message):
    from flask import render_template
    return render_template("public/index.html", error=message), 503
