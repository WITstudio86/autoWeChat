from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.student import Student
from app.models.course import CourseGroup

students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/")
@login_required
def list():
    group_id = request.args.get("group_id", type=int)
    sort = request.args.get("sort", "name")
    filter_text = request.args.get("filter", "").strip()

    query = Student.query.filter_by(teacher_id=current_user.id)

    if group_id:
        if group_id == -1:
            query = query.filter(Student.course_group_id.is_(None))
        else:
            query = query.filter_by(course_group_id=group_id)

    if filter_text:
        query = query.filter(Student.name.contains(filter_text))

    if sort == "time":
        query = query.join(CourseGroup, Student.course_group_id == CourseGroup.id, isouter=True)\
            .order_by(CourseGroup.day_of_week, CourseGroup.start_time, Student.name)
    else:
        query = query.order_by(Student.name)

    students = query.all()
    groups = CourseGroup.query.filter_by(teacher_id=current_user.id).order_by(CourseGroup.name).all()

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

        student = Student(
            teacher_id=current_user.id,
            name=name,
            parent_wechat=parent_wechat or None,
            course_group_id=course_group_id or None,
            phone=phone or None,
            notes=notes or None,
        )
        db.session.add(student)
        db.session.commit()
        flash(f"学员 {name} 添加成功", "success")
        return redirect(url_for("students.list"))

    groups = CourseGroup.query.filter_by(teacher_id=current_user.id).order_by(CourseGroup.name).all()
    return render_template("students/form.html", student=None, groups=groups)


@students_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    student = Student.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    groups = CourseGroup.query.filter_by(teacher_id=current_user.id).order_by(CourseGroup.name).all()

    if request.method == "POST":
        student.name = request.form.get("name", "").strip()
        student.parent_wechat = request.form.get("parent_wechat", "").strip() or None
        course_group_id = request.form.get("course_group_id", type=int)
        student.course_group_id = course_group_id or None
        student.phone = request.form.get("phone", "").strip() or None
        student.notes = request.form.get("notes", "").strip() or None

        if not student.name:
            flash("学员姓名不能为空", "danger")
            return render_template("students/form.html", student=student, groups=groups)

        db.session.commit()
        flash(f"学员 {student.name} 已更新", "success")
        return redirect(url_for("students.list"))

    return render_template("students/form.html", student=student, groups=groups)


@students_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    student = Student.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    db.session.delete(student)
    db.session.commit()
    flash(f"学员 {student.name} 已删除", "success")
    return redirect(url_for("students.list"))


@students_bp.route("/<int:id>/move", methods=["POST"])
@login_required
def move(id):
    student = Student.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    course_group_id = request.form.get("course_group_id", type=int)
    student.course_group_id = course_group_id or None
    db.session.commit()

    if request.headers.get("HX-Request"):
        group_name = student.course_group.name if student.course_group else "未分组"
        return f'<span class="badge bg-info">{group_name}</span>'

    flash(f"学员 {student.name} 已移动", "success")
    return redirect(url_for("students.list"))
