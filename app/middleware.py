from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, current_app


def login_required(f):
    """Decorator: check JWT in session. Redirect for pages, JSON 401 for API."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("jwt"):
            if _is_api_request():
                return jsonify({"error": "未登录或会话已过期，请刷新页面重新登录"}), 401
            flash("请先登录", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    """Decorator: check JWT in session, always return JSON 401."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("jwt"):
            return jsonify({"error": "未登录或会话已过期，请刷新页面重新登录"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: check admin flag in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("jwt"):
            if _is_api_request():
                return jsonify({"error": "未登录或会话已过期"}), 401
            return redirect(url_for("auth.login"))
        if not session.get("teacher", {}).get("is_admin"):
            flash("需要管理员权限", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


def _is_api_request():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("HX-Request") == "true"
        or request.headers.get("Accept", "").startswith("application/json")
    )
