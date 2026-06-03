from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware import login_required, admin_required
from app.api_client import api

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _get_usage_map():
    """Fetch monthly usage stats and index by teacher_id."""
    try:
        rows = api.admin_get_usage()
        return {r["teacher_id"]: r for r in rows}
    except Exception:
        return {}


@admin_bp.route("/")
@login_required
@admin_required
def index():
    teachers = api.admin_list_teachers()
    usage_map = _get_usage_map()
    return render_template("admin/teacher_list.html", teachers=teachers, usage=usage_map)


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

        data = {
            "username": username,
            "password": password,
            "display_name": display_name or None,
        }
        duration_months = request.form.get("duration_months", "").strip()
        if duration_months:
            data["duration_months"] = int(duration_months)

        max_groups = request.form.get("max_groups", "").strip()
        if max_groups:
            data["max_groups"] = int(max_groups)
        max_spg = request.form.get("max_students_per_group", "").strip()
        if max_spg:
            data["max_students_per_group"] = int(max_spg)

        try:
            api.admin_create_teacher(data)
            flash(f"教师账号 {username} 创建成功", "success")
            return redirect(url_for("admin.index"))
        except Exception as e:
            err = str(e)
            if "409" in err or "已存在" in err:
                flash("用户名已存在", "danger")
            else:
                flash(f"创建失败: {err}", "danger")
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

        data = {
            "display_name": display_name or None,
            "is_active": is_active,
        }
        duration_months = request.form.get("duration_months", "").strip()
        if duration_months:
            data["duration_months"] = int(duration_months)

        max_groups = request.form.get("max_groups", "").strip()
        data["max_groups"] = int(max_groups) if max_groups else None
        max_spg = request.form.get("max_students_per_group", "").strip()
        data["max_students_per_group"] = int(max_spg) if max_spg else None

        try:
            api.admin_update_teacher(id, data)
            flash(f"教师 {teacher['username']} 已更新", "success")
            return redirect(url_for("admin.index"))
        except Exception as e:
            flash(f"更新失败: {e}", "danger")

    return render_template("admin/teacher_form.html", teacher=teacher)


@admin_bp.route("/<int:id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(id):
    if id == session_get_teacher_id():
        flash("不能禁用自己", "danger")
        return redirect(url_for("admin.index"))
    try:
        result = api.admin_toggle_active(id)
        flash(result.get("message", "状态已切换"), "success")
    except Exception as e:
        flash(f"操作失败: {e}", "danger")
    return redirect(url_for("admin.index"))


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
