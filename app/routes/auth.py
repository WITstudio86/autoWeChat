from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.teacher import Teacher

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and teacher.check_password(password):
            if not teacher.is_active:
                flash("账号已被禁用，请联系管理员", "danger")
                return render_template("auth/login.html")

            login_user(teacher)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("用户名或密码错误", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    from app.extensions import db
    from app.models.settings import Settings

    user_settings = current_user.settings
    if not user_settings:
        user_settings = Settings(teacher_id=current_user.id)
        db.session.add(user_settings)
        db.session.flush()

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        current_user.display_name = display_name or None

        if password:
            if password != password2:
                flash("两次输入的密码不一致", "danger")
                return render_template("auth/settings.html", settings=user_settings)
            if len(password) < 6:
                flash("密码长度至少6位", "danger")
                return render_template("auth/settings.html", settings=user_settings)
            current_user.set_password(password)

        delay_ms = request.form.get("wechat_delay_ms", type=int)
        if delay_ms:
            user_settings.wechat_delay_ms = max(1000, min(10000, delay_ms))

        db.session.commit()
        flash("设置已更新", "success")
        return redirect(url_for("auth.settings"))

    return render_template("auth/settings.html", settings=user_settings)
