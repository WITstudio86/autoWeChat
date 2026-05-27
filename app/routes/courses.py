from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.course import CourseGroup, Course
from app.services.course_generator import generate_courses

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")

WEEKDAY_OPTIONS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@courses_bp.route("/")
@login_required
def list():
    groups = CourseGroup.query.filter_by(teacher_id=current_user.id)\
        .order_by(CourseGroup.created_at.desc()).all()
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

        group = CourseGroup(
            teacher_id=current_user.id,
            name=name,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        db.session.add(group)
        db.session.flush()

        new_courses = generate_courses(group, weeks_ahead=8)
        for course in new_courses:
            db.session.add(course)

        db.session.commit()
        flash(f"课程分组 '{name}' 创建成功，已自动生成 {len(new_courses)} 节课", "success")
        return redirect(url_for("courses.list"))

    return render_template("courses/form.html", group=None, weekdays=WEEKDAY_OPTIONS)


@courses_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    group = CourseGroup.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()

    if request.method == "POST":
        group.name = request.form.get("name", "").strip()
        group.day_of_week = request.form.get("day_of_week", "")
        group.start_time = request.form.get("start_time", "")
        group.end_time = request.form.get("end_time", "")

        if not all([group.name, group.day_of_week, group.start_time, group.end_time]):
            flash("所有字段不能为空", "danger")
            return render_template("courses/form.html", group=group, weekdays=WEEKDAY_OPTIONS)

        db.session.commit()
        flash("课程分组已更新", "success")
        return redirect(url_for("courses.list"))

    return render_template("courses/form.html", group=group, weekdays=WEEKDAY_OPTIONS)


@courses_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    group = CourseGroup.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    db.session.delete(group)
    db.session.commit()
    flash(f"课程分组 '{group.name}' 已删除", "success")
    return redirect(url_for("courses.list"))


@courses_bp.route("/<int:id>/calendar")
@login_required
def calendar(id):
    group = CourseGroup.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    courses = Course.query.filter_by(course_group_id=id)\
        .order_by(Course.date).all()
    return render_template("courses/calendar.html", group=group, courses=courses)


@courses_bp.route("/<int:id>/generate", methods=["POST"])
@login_required
def generate(id):
    group = CourseGroup.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    weeks = int(request.form.get("weeks", 4))
    new_courses = generate_courses(group, weeks_ahead=weeks)
    for course in new_courses:
        db.session.add(course)
    db.session.commit()
    flash(f"已生成 {len(new_courses)} 节新课程", "success")
    return redirect(url_for("courses.calendar", id=id))


@courses_bp.route("/instance/<int:id>/status", methods=["POST"])
@login_required
def update_status(id):
    course = Course.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    new_status = request.form.get("status", "upcoming")
    if new_status in ("upcoming", "completed", "cancelled"):
        course.status = new_status
        db.session.commit()
    return redirect(url_for("courses.calendar", id=course.course_group_id))
