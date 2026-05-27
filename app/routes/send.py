import uuid
import threading
from datetime import date
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.student import Student
from app.models.template import NotificationTemplate
from app.models.course import CourseGroup, Course
from app.models.send_log import SendLog
from app.services.message_renderer import render_message
from app.services.ai_generator import generate_autocontent, generate_performance
from app.services.wechat_sender import send_message, WeChatSendError

send_bp = Blueprint("send", __name__, url_prefix="/send")

# In-memory job store
_jobs = {}
_job_lock = threading.Lock()


def api_login_required(f):
    """类似 @login_required，但返回 JSON 而非重定向到登录页"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "未登录或会话已过期，请刷新页面重新登录"}), 401
        return f(*args, **kwargs)
    return decorated


@send_bp.route("/")
@login_required
def index():
    templates = NotificationTemplate.query.filter_by(teacher_id=current_user.id)\
        .order_by(NotificationTemplate.updated_at.desc()).all()
    groups = CourseGroup.query.filter_by(teacher_id=current_user.id)\
        .order_by(CourseGroup.name).all()
    students = Student.query.filter_by(teacher_id=current_user.id)\
        .order_by(Student.name).all()
    return render_template("send/index.html",
                          templates=templates,
                          groups=groups,
                          students=students)


@send_bp.route("/start", methods=["POST"])
@api_login_required
def start():
    template_id = request.form.get("template_id", type=int)
    student_ids = request.form.getlist("student_ids", type=int)
    course_id = request.form.get("course_id", type=int)

    if not template_id or not student_ids:
        return jsonify({"error": "请选择模板和至少一名学员"}), 400

    template = NotificationTemplate.query.filter_by(
        id=template_id, teacher_id=current_user.id).first()
    if not template:
        return jsonify({"error": "模板不存在"}), 404

    students = Student.query.filter(
        Student.id.in_(student_ids),
        Student.teacher_id == current_user.id
    ).all()
    if not students:
        return jsonify({"error": "未找到有效学员"}), 404

    course_time = ""
    course_date_str = ""
    weekday_str = ""
    if course_id:
        course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
        if course and course.group:
            group = course.group
            course_time = group.time_display
            course_date_str = course.date.strftime("%Y-%m-%d")
            weekday_str = course.weekday_display

    autocontent_description = request.form.get("autocontent_description", "").strip()
    performance_notes = {}
    has_performance = "{performance}" in template.content
    if has_performance:
        for sid in student_ids:
            note = request.form.get(f"performance_{sid}", "").strip()
            if note:
                performance_notes[int(sid)] = note

    delay_ms = 2500
    teacher_settings = current_user.settings
    if teacher_settings:
        delay_ms = teacher_settings.wechat_delay_ms or 2500

    teacher_name = current_user.display_name or current_user.username
    teacher_id = current_user.id

    # 从 app config 获取 AI 配置，传给后台线程（线程内无法访问 current_app）
    from flask import current_app as _app
    ai_key = _app.config.get("AI_API_KEY", "")
    ai_endpoint = _app.config.get("AI_API_ENDPOINT", "https://api.deepseek.com/v1")
    ai_model = _app.config.get("AI_MODEL", "deepseek-v4-flash")

    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "total": len(students),
        "completed": 0,
        "failed": 0,
        "status": "running",
        "current": "",
        "logs": [],
    }

    with _job_lock:
        _jobs[job_id] = job

    thread = threading.Thread(
        target=_run_send_job,
        args=(job_id, teacher_id, teacher_name, template, students,
              autocontent_description, performance_notes,
              course_time, course_date_str, weekday_str, delay_ms,
              ai_key, ai_endpoint, ai_model),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@send_bp.route("/status/<job_id>")
@api_login_required
def status(job_id):
    with _job_lock:
        job = _jobs.get(job_id)

    if not job:
        return jsonify({"status": "not_found"}), 404

    return jsonify({
        "total": job["total"],
        "completed": job["completed"],
        "failed": job["failed"],
        "status": job["status"],
        "current": job["current"],
    })


@send_bp.route("/history")
@login_required
def history():
    logs = SendLog.query.filter_by(teacher_id=current_user.id)\
        .order_by(SendLog.sent_at.desc()).limit(100).all()
    return render_template("send/history.html", logs=logs)


def _run_send_job(job_id, teacher_id, teacher_name, template, students,
                  autocontent_description, performance_notes,
                  course_time, course_date_str, weekday_str, delay_ms,
                  ai_key, ai_endpoint, ai_model):
    with _job_lock:
        job = _jobs.get(job_id)
    if not job:
        return

    has_autocontent = "{autocontent}" in template.content
    has_performance = "{performance}" in template.content

    autocontent = ""
    if has_autocontent:
        autocontent = generate_autocontent(autocontent_description or "")

    for student in students:
        try:
            with _job_lock:
                job["current"] = student.name

            perf = ""
            if has_performance:
                notes = performance_notes.get(student.id, "")
                perf = generate_performance(student.name, notes)

            message = render_message(
                template_content=template.content,
                student_name=student.name,
                course_time=course_time,
                course_date=course_date_str,
                weekday=weekday_str,
                teacher_name=teacher_name,
                autocontent=autocontent,
                performance=perf,
            )

            log = SendLog(
                teacher_id=teacher_id,
                student_id=student.id,
                template_id=template.id,
                message_content=message,
                status="success",
            )

            try:
                contact = student.parent_wechat or student.name
                send_message(contact, message, delay_ms)
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
                with _job_lock:
                    job["failed"] += 1
            else:
                with _job_lock:
                    job["completed"] += 1

            db.session.add(log)
            db.session.commit()
        except Exception as e:
            with _job_lock:
                job["failed"] += 1
            try:
                db.session.rollback()
            except Exception:
                pass

    with _job_lock:
        job["status"] = "done"
        job["current"] = ""
