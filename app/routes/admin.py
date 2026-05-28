from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware import login_required, admin_required
from app.api_client import api

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def index():
    teachers = api.admin_list_teachers()
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

        try:
            api.admin_create_teacher({
                "username": username,
                "password": password,
                "display_name": display_name or None,
            })
            flash(f"教师账号 {username} 创建成功", "success")
            return redirect(url_for("admin.index"))
        except Exception as e:
            err = str(e)
            if "409" in err or "已存在" in err:
                flash("用户名已存在", "danger")
            else:
                flash("创建失败", "danger")
            return render_template("admin/teacher_form.html", teacher=None)

    return render_template("admin/teacher_form.html", teacher=None)


@admin_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(id):
    teachers = api.admin_list_teachers()
    teacher = next((t for t in teachers if t["id"] == id), None)
    if not teacher:
        flash("教师不存在", "danger")
        return redirect(url_for("admin.index"))

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        is_active = request.form.get("is_active") == "on"

        if teacher["id"] == session_get_teacher_id() and not is_active:
            flash("不能禁用自己的账号", "danger")
            return render_template("admin/teacher_form.html", teacher=teacher)

        try:
            api.admin_update_teacher(id, {
                "display_name": display_name or None,
                "is_active": is_active,
            })
            flash(f"教师 {teacher['username']} 已更新", "success")
            return redirect(url_for("admin.index"))
        except Exception:
            flash("更新失败", "danger")

    return render_template("admin/teacher_form.html", teacher=teacher)


@admin_bp.route("/<int:id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(id):
    new_password = request.form.get("new_password", "")

    if not new_password or len(new_password) < 6:
        flash("密码长度至少6位", "danger")
        return redirect(url_for("admin.index"))

    try:
        api.admin_reset_password(id, new_password)
        flash("密码已重置", "success")
    except Exception:
        flash("重置密码失败", "danger")
    return redirect(url_for("admin.index"))


@admin_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(id):
    if id == session_get_teacher_id():
        flash("不能删除自己的账号", "danger")
        return redirect(url_for("admin.index"))

    try:
        api.admin_delete_teacher(id)
        flash("教师已删除", "success")
    except Exception:
        flash("删除失败", "danger")
    return redirect(url_for("admin.index"))


def session_get_teacher_id():
    from flask import session
    return session.get("teacher", {}).get("id")
