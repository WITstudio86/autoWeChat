from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models.teacher import Teacher

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("需要管理员权限", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def index():
    teachers = Teacher.query.order_by(Teacher.created_at.desc()).all()
    return render_template("admin/teacher_list.html", teachers=teachers)


@admin_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip()

        if not username or not password:
            flash("用户名和密码不能为空", "danger")
            return render_template("admin/teacher_form.html", teacher=None)

        if Teacher.query.filter_by(username=username).first():
            flash("用户名已存在", "danger")
            return render_template("admin/teacher_form.html", teacher=None)

        teacher = Teacher(
            username=username,
            display_name=display_name or None,
        )
        teacher.set_password(password)
        db.session.add(teacher)
        db.session.commit()
        flash(f"教师账号 {username} 创建成功", "success")
        return redirect(url_for("admin.index"))

    return render_template("admin/teacher_form.html", teacher=None)


@admin_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(id):
    teacher = Teacher.query.get_or_404(id)

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        is_active = request.form.get("is_active") == "on"

        if teacher.id == current_user.id and not is_active:
            flash("不能禁用自己的账号", "danger")
            return render_template("admin/teacher_form.html", teacher=teacher)

        teacher.display_name = display_name or None
        teacher.is_active = is_active
        db.session.commit()
        flash(f"教师 {teacher.username} 已更新", "success")
        return redirect(url_for("admin.index"))

    return render_template("admin/teacher_form.html", teacher=teacher)


@admin_bp.route("/<int:id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(id):
    teacher = Teacher.query.get_or_404(id)
    new_password = request.form.get("new_password", "")

    if not new_password or len(new_password) < 6:
        flash("密码长度至少6位", "danger")
        return redirect(url_for("admin.index"))

    teacher.set_password(new_password)
    db.session.commit()
    flash(f"教师 {teacher.username} 的密码已重置", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(id):
    teacher = Teacher.query.get_or_404(id)

    if teacher.id == current_user.id:
        flash("不能删除自己的账号", "danger")
        return redirect(url_for("admin.index"))

    db.session.delete(teacher)
    db.session.commit()
    flash(f"教师 {teacher.username} 已删除", "success")
    return redirect(url_for("admin.index"))
