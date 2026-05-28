from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware import login_required
from app.api_client import api

students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/")
@login_required
def list():
    group_id = request.args.get("group_id", type=int)
    sort = request.args.get("sort", "name")
    filter_text = request.args.get("filter", "").strip()

    students = api.list_students(group_id=group_id, sort=sort, filter_text=filter_text)
    groups = api.list_groups()

    return render_template("students/list.html",
                          students=students,
                          groups=groups,
                          current_group_id=group_id,
                          current_sort=sort,
                          current_filter=filter_text)


@students_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        parent_wechat = request.form.get("parent_wechat", "").strip()
        course_group_id = request.form.get("course_group_id", type=int)
        phone = request.form.get("phone", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name:
            flash("学员姓名不能为空", "danger")
            return redirect(url_for("students.create"))

        api.create_student({
            "name": name,
            "parent_wechat": parent_wechat or None,
            "course_group_id": course_group_id or None,
            "phone": phone or None,
            "notes": notes or None,
        })
        flash(f"学员 {name} 添加成功", "success")
        return redirect(url_for("students.list"))

    groups = api.list_groups()
    return render_template("students/form.html", student=None, groups=groups)


@students_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    try:
        student = api.get_student(id)
    except Exception:
        flash("学员不存在", "danger")
        return redirect(url_for("students.list"))

    groups = api.list_groups()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        parent_wechat = request.form.get("parent_wechat", "").strip() or None
        course_group_id = request.form.get("course_group_id", type=int)
        phone = request.form.get("phone", "").strip() or None
        notes = request.form.get("notes", "").strip() or None

        if not name:
            flash("学员姓名不能为空", "danger")
            return render_template("students/form.html", student=student, groups=groups)

        api.update_student(id, {
            "name": name,
            "parent_wechat": parent_wechat,
            "course_group_id": course_group_id or None,
            "phone": phone,
            "notes": notes,
        })
        flash(f"学员 {name} 已更新", "success")
        return redirect(url_for("students.list"))

    return render_template("students/form.html", student=student, groups=groups)


@students_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    try:
        student = api.get_student(id)
        api.delete_student(id)
        flash(f"学员 {student['name']} 已删除", "success")
    except Exception:
        flash("删除失败", "danger")
    return redirect(url_for("students.list"))


@students_bp.route("/<int:id>/move", methods=["POST"])
@login_required
def move(id):
    course_group_id = request.form.get("course_group_id", type=int)
    try:
        student = api.move_student(id, course_group_id or None)
    except Exception:
        flash("移动失败", "danger")
        return redirect(url_for("students.list"))

    if request.headers.get("HX-Request"):
        group_name = "未分组"
        if student.get("course_group_id"):
            groups = api.list_groups()
            for g in groups:
                if g["id"] == student["course_group_id"]:
                    group_name = g["name"]
                    break
        return f'<span class="badge bg-info">{group_name}</span>'

    flash(f"学员 {student['name']} 已移动", "success")
    return redirect(url_for("students.list"))
