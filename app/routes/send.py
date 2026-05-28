import hashlib
import os
import time
import uuid
import threading
from flask import Blueprint, render_template, request, jsonify, send_file, session, current_app
from app.middleware import login_required, api_login_required
from app.api_client import api
from app.services.ai_generator import generate_autocontent, generate_performance
from app.services.message_renderer import render_message
from app.services.wechat_sender import send_message, WeChatSendError
from app.services.screenshot import capture_wechat_window, stitch_images, _get_wechat_window_id

send_bp = Blueprint("send", __name__, url_prefix="/send")

# In-memory job tracking
_jobs = {}


def _run_send_job(job_id, teacher_name, template, students,
                  autocontent_description, performance_notes,
                  course_time, course_date_str, weekday_str, course_id,
                  jwt_token, server_base_url, instance_path,
                  app_name, delay_ms):
    """Background thread: generate AI content, send WeChat messages, capture screenshots."""
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = "running"

    # Use a thread-local API client with explicit JWT and base_url
    from app.api_client import ApiClient
    thread_api = ApiClient(base_url=server_base_url)
    thread_api._headers = lambda extra=None: {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        **(extra or {}),
    }

    # 1. Generate autocontent once for all students
    autocontent = ""
    if autocontent_description:
        autocontent = generate_autocontent(autocontent_description)

    screenshot_paths = []

    for student in students:
        if job.get("_cancelled"):
            break

        job["current_student"] = student["name"]

        # 2. Generate performance note for this student
        performance = ""
        sid = str(student["id"])
        if performance_notes and sid in performance_notes:
            performance = generate_performance(student["name"], performance_notes[sid])

        # 3. Render message
        message = render_message(
            template_content=template["content"],
            student_name=student["name"],
            course_time=course_time,
            course_date=course_date_str,
            weekday=weekday_str,
            teacher_name=teacher_name,
            autocontent=autocontent,
            performance=performance,
        )

        # 4. Send via WeChat
        status = "success"
        error = None
        contact = student.get("parent_wechat") or student["name"]
        try:
            send_message(contact, message, delay_ms=delay_ms, app_name=app_name)
        except WeChatSendError as e:
            status = "failed"
            error = str(e)
        except Exception as e:
            status = "failed"
            error = str(e)

        # 5. Capture screenshot after send
        screenshot_path = None
        if status == "success":
            screenshot_dir = os.path.join(instance_path, "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, f"{job_id}_{student['id']}.png")
            if capture_wechat_window(filepath, app_name=app_name):
                screenshot_path = filepath
                screenshot_paths.append(filepath)

        # 6. Save SendLog via Node.js API
        log_data = {
            "student_id": student["id"],
            "template_id": template["id"],
            "course_id": course_id,
            "message_content": message,
            "status": status,
            "error_message": error,
            "screenshot_path": screenshot_path,
        }
        try:
            thread_api.create_send_log(log_data)
        except Exception:
            pass  # Log failure shouldn't block the send flow

        job["completed_count"] += 1
        if status == "failed":
            job["failed_count"] += 1

        time.sleep(1)

    # 7. Stitch screenshots into one long image
    if screenshot_paths:
        stitch_dir = os.path.join(instance_path, "stitched")
        os.makedirs(stitch_dir, exist_ok=True)
        stitch_path = os.path.join(stitch_dir, f"{job_id}.png")
        stitch_images(screenshot_paths, stitch_path)
        job["stitched_path"] = stitch_path

    job["status"] = "done"
    job["current_student"] = ""


@send_bp.route("/")
@login_required
def index():
    templates = api.list_templates()
    groups = api.list_groups()
    students = api.list_students()

    # Build group->courses mapping for the course selector
    groups_with_courses = []
    for g in groups:
        try:
            courses = api.list_courses(g["id"])
            g["courses"] = courses
        except Exception:
            g["courses"] = []
        groups_with_courses.append(g)

    try:
        settings = api.get_settings()
    except Exception:
        settings = {}

    return render_template("send/index.html",
                          templates=templates,
                          groups=groups_with_courses,
                          students=students,
                          target_app_name=settings.get("target_app_name", "WeChat"))


@send_bp.route("/start", methods=["POST"])
@api_login_required
def start():
    template_id = request.form.get("template_id", type=int)
    student_ids = request.form.getlist("student_ids", type=int)
    course_id = request.form.get("course_id", type=int)

    if not template_id or not student_ids:
        return jsonify({"error": "请选择模板和至少一名学员"}), 400

    try:
        template = api.get_template(template_id)
    except Exception:
        return jsonify({"error": "模板不存在"}), 404

    # Get all students for this teacher and filter to selected IDs
    all_students = api.list_students()
    students = [s for s in all_students if s["id"] in student_ids]
    if not students:
        return jsonify({"error": "未找到有效学员"}), 404

    course_time = ""
    course_date_str = ""
    weekday_str = ""
    if course_id:
        try:
            api.update_course_status(course_id, "upcoming")  # Verify course exists
            # Get course group for time display
            groups = api.list_groups()
            for g in groups:
                for c in api.list_courses(g["id"]):
                    if c["id"] == course_id:
                        course_time = g.get("time_display", "")
                        course_date_str = c.get("date", "")
                        weekday_str = c.get("weekday_display", "")
                        break
                if course_time:
                    break
        except Exception:
            pass

    autocontent_description = request.form.get("autocontent_description", "").strip()
    performance_notes = {}
    has_performance = "{performance}" in template["content"]
    if has_performance:
        for sid in student_ids:
            note = request.form.get(f"performance_{sid}", "").strip()
            if note:
                performance_notes[str(sid)] = note

    teacher = session.get("teacher", {})
    teacher_name = teacher.get("display_name") or teacher.get("username", "")

    # Read settings for app_name and delay
    try:
        settings = api.get_settings()
    except Exception:
        settings = {}
    app_name = request.form.get("app_name", "").strip() or settings.get("target_app_name", "WeChat")
    delay_ms = settings.get("wechat_delay_ms", 2500)

    # Create in-memory job and start background thread
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "total_count": len(students),
        "completed_count": 0,
        "failed_count": 0,
        "status": "pending",
        "current_student": "",
        "stitched_path": None,
    }

    jwt_token = session.get("jwt", "")
    server_base_url = current_app.config["SERVER_BASE_URL"]

    thread = threading.Thread(
        target=_run_send_job,
        args=(job_id, teacher_name, template, students,
              autocontent_description, performance_notes,
              course_time, course_date_str, weekday_str, course_id,
              jwt_token, server_base_url, current_app.instance_path,
              app_name, delay_ms),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@send_bp.route("/status/<job_id>")
@api_login_required
def status(job_id):
    job = _jobs.get(job_id)

    if not job:
        return jsonify({"status": "not_found"}), 404

    return jsonify({
        "total": job["total_count"],
        "completed": job["completed_count"],
        "failed": job["failed_count"],
        "status": job["status"],
        "current": job["current_student"] or "",
        "stitched_available": bool(job.get("stitched_path")),
    })


@send_bp.route("/stitched/<job_id>")
@login_required
def download_stitched(job_id):
    job = _jobs.get(job_id)
    if not job or not job.get("stitched_path"):
        return jsonify({"error": "长图不存在或尚未生成"}), 404

    if not os.path.exists(job["stitched_path"]):
        return jsonify({"error": "长图文件已丢失"}), 404

    return send_file(
        job["stitched_path"],
        mimetype="image/png",
        as_attachment=True,
        download_name=f"发送记录长图_{job_id}.png",
    )


@send_bp.route("/test-window", methods=["POST"])
@api_login_required
def test_window():
    """Take a test screenshot of the target app window."""
    import subprocess as sp

    app_name = request.form.get("app_name", "WeChat").strip()
    if not app_name:
        return jsonify({"error": "请输入应用名称"}), 400

    instance_path = current_app.instance_path
    test_dir = os.path.join(instance_path, "screenshots")
    os.makedirs(test_dir, exist_ok=True)

    # Activate the target app
    sp.call(["open", "-a", app_name], timeout=5)
    time.sleep(1.5)  # Wait for window to settle (longer for Stage Manager)

    # Get window ID and capture
    win_id = _get_wechat_window_id(app_name)

    filename = f"test_{hashlib.md5(app_name.encode()).hexdigest()[:8]}.png"
    filepath = os.path.join(test_dir, filename)

    if win_id is not None:
        sp.call(["screencapture", "-x", "-l", str(win_id), filepath], timeout=5)
    else:
        # Fallback: full screen capture
        sp.call(["screencapture", "-x", filepath], timeout=5)

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return jsonify({"error": f"未能捕获 '{app_name}' 的窗口，请确认应用已打开"}), 400

    return jsonify({
        "success": True,
        "image_url": f"/send/test-image/{filename}",
        "app_name": app_name,
    })


@send_bp.route("/test-image/<filename>")
@login_required
def test_image(filename):
    """Serve a test screenshot."""
    instance_path = current_app.instance_path
    filepath = os.path.join(instance_path, "screenshots", filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "文件不存在"}), 404
    return send_file(filepath, mimetype="image/png")


@send_bp.route("/history")
@login_required
def history():
    logs = api.list_send_logs(limit=100)
    return render_template("send/history.html", logs=logs)
