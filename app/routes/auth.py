from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.api_client import api
from app.middleware import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("jwt"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            result = api.login(username, password)
            session["jwt"] = result["token"]
            session["jwt_exp"] = result["expires_at"]
            session["teacher"] = result["teacher"]
            session.permanent = True

            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        except Exception:
            flash("用户名或密码错误", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    api.logout()
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    try:
        user_settings = api.get_settings()
    except Exception:
        user_settings = {}

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        # Update display_name on server
        if display_name:
            try:
                api.admin_update_teacher(session["teacher"]["id"], {"display_name": display_name})
                session["teacher"]["display_name"] = display_name or None
            except Exception:
                flash("更新显示名称失败", "danger")

        # Password change - not supported via Node.js API for self-service yet,
        # use admin reset-password endpoint
        if password:
            if password != password2:
                flash("两次输入的密码不一致", "danger")
                return render_template("auth/settings.html", settings=user_settings)
            if len(password) < 6:
                flash("密码长度至少6位", "danger")
                return render_template("auth/settings.html", settings=user_settings)
            try:
                api.admin_reset_password(session["teacher"]["id"], password)
                flash("密码已更新，请重新登录", "success")
                session.clear()
                return redirect(url_for("auth.login"))
            except Exception:
                flash("修改密码失败", "danger")

        delay_ms = request.form.get("wechat_delay_ms", type=int)
        target_app_name = request.form.get("target_app_name", "").strip()

        updates = {}
        if delay_ms:
            updates["wechat_delay_ms"] = max(1000, min(10000, delay_ms))
        if target_app_name:
            updates["target_app_name"] = target_app_name

        if updates:
            try:
                api.update_settings(updates)
                for k, v in updates.items():
                    user_settings[k] = v
                flash("设置已更新", "success")
            except Exception:
                flash("保存设置失败", "danger")

        return redirect(url_for("auth.settings"))

    return render_template("auth/settings.html", settings=user_settings)
