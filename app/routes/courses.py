from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware import login_required
from app.api_client import api

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")

WEEKDAY_OPTIONS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@courses_bp.route("/")
@login_required
def list():
    groups = api.list_groups()
    return render_template("courses/list.html", groups=groups)


@courses_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        day_of_week = request.form.get("day_of_week", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")

        if not all([name, day_of_week, start_time, end_time]):
            flash("所有字段不能为空", "danger")
            return render_template("courses/form.html", group=None, weekdays=WEEKDAY_OPTIONS)

        if day_of_week not in WEEKDAY_OPTIONS:
            flash("请选择有效的星期", "danger")
            return render_template("courses/form.html", group=None, weekdays=WEEKDAY_OPTIONS)

        api.create_group({
            "name": name,
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
        })
        flash(f"课程分组 '{name}' 创建成功", "success")
        return redirect(url_for("courses.list"))

    return render_template("courses/form.html", group=None, weekdays=WEEKDAY_OPTIONS)


@courses_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    try:
        group = api.get_group(id)
    except Exception:
        flash("分组不存在", "danger")
        return redirect(url_for("courses.list"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        day_of_week = request.form.get("day_of_week", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")

        if not all([name, day_of_week, start_time, end_time]):
            flash("所有字段不能为空", "danger")
            return render_template("courses/form.html", group=group, weekdays=WEEKDAY_OPTIONS)

        api.update_group(id, {
            "name": name,
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
        })
        flash("课程分组已更新", "success")
        return redirect(url_for("courses.list"))

    return render_template("courses/form.html", group=group, weekdays=WEEKDAY_OPTIONS)


@courses_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    try:
        group = api.get_group(id)
        api.delete_group(id)
        flash(f"课程分组 '{group['name']}' 已删除", "success")
    except Exception:
        flash("删除失败", "danger")
    return redirect(url_for("courses.list"))

