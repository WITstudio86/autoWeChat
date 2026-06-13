import hashlib
import json
import os
import platform
import time
import uuid
import base64
import tempfile
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
_generated = {}


def _run_send_job(job_id, teacher_name, template, students,
                  autocontent_description, performance_notes,
                  pre_generated_messages,
                  jwt_token, server_base_url, instance_path,
                  app_name, delay_ms, attachment_paths=None,
                  homework=""):
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

    # Use pre-generated messages if available, otherwise generate AI content
    if pre_generated_messages:
        messages_map = {str(m["student_id"]): m["message"] for m in pre_generated_messages}
    else:
        messages_map = {}
        # 1. Generate autocontent once for all students
        autocontent = ""
        if autocontent_description:
            autocontent = generate_autocontent(autocontent_description)

        for student in students:
            sid = str(student["id"])
            performance = ""
            if performance_notes and sid in performance_notes:
                performance = generate_performance(student["name"], performance_notes[sid],
                                                     course_context=autocontent_description)

            message = render_message(
                template_content=template["content"],
                student_name=student["name"],
                course_time="",
                course_date="",
                weekday="",
                teacher_name=teacher_name,
                autocontent=autocontent,
                performance=performance,
                homework=homework,
            )
            messages_map[sid] = message

    screenshot_paths = []

    for i, student in enumerate(students):
        if job.get("_cancelled"):
            break

        sid = str(student["id"])
        job["current_student"] = f"({i + 1}/{len(students)}) {student['name']}"

        # Get message from pre-generated map
        message = messages_map.get(sid, "")
        if not message:
            job["completed_count"] += 1
            job["failed_count"] += 1
            continue

        # Send via WeChat
        status = "success"
        error = None
        contact = student.get("parent_wechat") or student["name"]
        job["current_student"] = f"({i + 1}/{len(students)}) 发送中: {student['name']}"
        try:
            send_message(contact, message, delay_ms=delay_ms, app_name=app_name,
                             attachments=attachment_paths)
        except WeChatSendError as e:
            status = "failed"
            error = str(e)
        except Exception as e:
            status = "failed"
            error = str(e)

        # Capture screenshot after send
        screenshot_path = None
        if status == "success":
            job["current_student"] = f"({i + 1}/{len(students)}) 截图中: {student['name']}"
            screenshot_dir = os.path.join(instance_path, "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, f"{job_id}_{student['id']}.png")
            if capture_wechat_window(filepath, app_name=app_name):
                screenshot_path = filepath
                screenshot_paths.append(filepath)

        # Save SendLog via Node.js API
        log_data = {
            "student_id": student["id"],
            "template_id": template["id"],
            "course_id": None,
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

        time.sleep(0.5)

    # Stitch screenshots into one long image
    if screenshot_paths:
        stitch_dir = os.path.join(instance_path, "stitched")
        os.makedirs(stitch_dir, exist_ok=True)
        stitch_path = os.path.join(stitch_dir, f"{job_id}.png")
        stitch_images(screenshot_paths, stitch_path)
        job["stitched_path"] = stitch_path

    # Switch back to browser so user can see results
    _activate_browser(job.get("_browser"))

    if not job.get("_cancelled"):
        job["status"] = "done"
    job["current_student"] = ""


def _detect_browser(user_agent):
    """Map User-Agent string to macOS app name for open -a."""
    ua = user_agent.lower()
    if "edg/" in ua:
        return "Microsoft Edge"
    if "chrome/" in ua:
        return "Google Chrome"
    if "safari/" in ua and "chrome/" not in ua:
        return "Safari"
    if "firefox/" in ua:
        return "Firefox"
    return None


def _activate_browser(browser_name=None):
    """Bring the browser back to front after sending completes."""
    import subprocess as sp
    if platform.system() != "Darwin":
        return
    candidates = []
    if browser_name:
        candidates.append(browser_name)
    candidates.extend(["Google Chrome", "Safari", "Microsoft Edge", "Firefox"])
    for browser in candidates:
        rc = sp.call(["open", "-a", browser], timeout=3)
        if rc == 0:
            break


@send_bp.route("/")
@login_required
def index():
    templates = api.list_templates()
    groups = api.list_groups()
    students = api.list_students()

    try:
        settings = api.get_settings()
    except Exception:
        settings = {}

    return render_template("send/index.html",
                          templates=templates,
                          groups=groups,
                          students=students,
                          target_app_name=settings.get("target_app_name", "WeChat"))


@send_bp.route("/start", methods=["POST"])
@api_login_required
def start():
    template_id = request.form.get("template_id", type=int)
    student_ids = request.form.getlist("student_ids", type=int)
    generate_id = request.form.get("generate_id", "").strip()

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

    # Use pre-generated or edited messages if available
    pre_generated = None
    messages_json = request.form.get("messages_json", "").strip()
    if messages_json:
        try:
            pre_generated = json.loads(messages_json)
            # Clean up cached version if exists
            if generate_id and generate_id in _generated:
                _generated.pop(generate_id)
        except (json.JSONDecodeError, ValueError):
            pass
    elif generate_id and generate_id in _generated:
        pre_generated = _generated.pop(generate_id)

    autocontent_description = request.form.get("autocontent_description", "").strip()
    homework = request.form.get("homework", "").strip()
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

    # Collect attachment paths
    attachment_paths = request.form.getlist("attachment_paths[]")

    # Create in-memory job and start background thread
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "total_count": len(students),
        "completed_count": 0,
        "failed_count": 0,
        "status": "pending",
        "current_student": "",
        "stitched_path": None,
        "_browser": _detect_browser(request.headers.get("User-Agent", "")),
    }

    jwt_token = session.get("jwt", "")
    server_base_url = current_app.config["SERVER_BASE_URL"]

    thread = threading.Thread(
        target=_run_send_job,
        args=(job_id, teacher_name, template, students,
              autocontent_description, performance_notes,
              pre_generated,
              jwt_token, server_base_url, current_app.instance_path,
              app_name, delay_ms, attachment_paths, homework),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@send_bp.route("/generate", methods=["POST"])
@api_login_required
def generate():
    """Generate messages for all selected students without sending."""
    template_id = request.form.get("template_id", type=int)
    student_ids = request.form.getlist("student_ids", type=int)

    if not template_id or not student_ids:
        return jsonify({"error": "请选择模板和至少一名学员"}), 400

    try:
        template = api.get_template(template_id)
    except Exception:
        return jsonify({"error": "模板不存在"}), 404

    all_students = api.list_students()
    students = [s for s in all_students if s["id"] in student_ids]
    if not students:
        return jsonify({"error": "未找到有效学员"}), 404

    autocontent_description = request.form.get("autocontent_description", "").strip()
    homework = request.form.get("homework", "").strip()
    performance_notes = {}
    has_performance = "{performance}" in template["content"]
    if has_performance:
        for sid in student_ids:
            note = request.form.get(f"performance_{sid}", "").strip()
            if note:
                performance_notes[str(sid)] = note

    teacher = session.get("teacher", {})
    teacher_name = teacher.get("display_name") or teacher.get("username", "")

    # Generate autocontent once
    autocontent = ""
    if autocontent_description:
        autocontent = generate_autocontent(autocontent_description)

    # Generate performance and render message for each student
    messages = []
    for student in students:
        sid = str(student["id"])
        performance = ""
        if performance_notes and sid in performance_notes:
            performance = generate_performance(student["name"], performance_notes[sid],
                                                 course_context=autocontent_description)

        message = render_message(
            template_content=template["content"],
            student_name=student["name"],
            course_time="",
            course_date="",
            weekday="",
            teacher_name=teacher_name,
            autocontent=autocontent,
            performance=performance,
            homework=homework,
        )
        messages.append({
            "student_id": student["id"],
            "student_name": student["name"],
            "message": message,
        })

    # Store generated messages
    generate_id = uuid.uuid4().hex[:12]
    _generated[generate_id] = messages

    return jsonify({
        "generate_id": generate_id,
        "messages": messages,
    })


@send_bp.route("/cancel/<job_id>", methods=["POST"])
@api_login_required
def cancel(job_id):
    """Cancel a running send job."""
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "任务不存在"}), 404
    if job["status"] in ("done", "cancelled"):
        return jsonify({"error": "任务已结束，无法中断"}), 400

    job["_cancelled"] = True
    job["status"] = "cancelled"
    return jsonify({"success": True})


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
    app_name = request.form.get("app_name", "WeChat").strip()
    if not app_name:
        return jsonify({"error": "请输入应用名称"}), 400

    instance_path = current_app.instance_path
    test_dir = os.path.join(instance_path, "screenshots")
    os.makedirs(test_dir, exist_ok=True)

    filename = f"test_{hashlib.md5(app_name.encode()).hexdigest()[:8]}.png"
    filepath = os.path.join(test_dir, filename)

    if platform.system() == "Darwin":
        _test_window_mac(app_name, filepath)
    elif platform.system() == "Windows":
        _test_window_windows(app_name, filepath)
    else:
        return jsonify({"error": "当前系统不支持窗口测试"}), 400

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return jsonify({"error": f"未能捕获 '{app_name}' 的窗口，请确认应用已打开"}), 400

    # Switch back to browser
    _activate_browser(_detect_browser(request.headers.get("User-Agent", "")))

    return jsonify({
        "success": True,
        "image_url": f"/send/test-image/{filename}",
        "app_name": app_name,
    })


def _test_window_mac(app_name, filepath):
    """Test screenshot on macOS using screencapture."""
    import subprocess as sp
    sp.call(["open", "-a", app_name], timeout=5)
    time.sleep(1.5)
    win_id, _, _ = _get_wechat_window_id(app_name)
    if win_id is not None:
        sp.call(["screencapture", "-x", "-l", str(win_id), filepath], timeout=5)
    else:
        sp.call(["screencapture", "-x", filepath], timeout=5)


def _test_window_windows(app_name, filepath):
    """Test screenshot on Windows using pyautogui."""
    import subprocess as sp
    sp.call(["start", app_name], shell=True)
    time.sleep(1.5)
    import pyautogui
    img = pyautogui.screenshot()
    img.save(filepath)


@send_bp.route("/test-image/<filename>")
@login_required
def test_image(filename):
    """Serve a test screenshot."""
    instance_path = current_app.instance_path
    filepath = os.path.join(instance_path, "screenshots", filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "文件不存在"}), 404
    return send_file(filepath, mimetype="image/png")


def _get_attachment_dir():
    """Ensure the temp attachment directory exists and return its path."""
    attachment_dir = os.path.join(tempfile.gettempdir(), "autoWeChat_attachments")
    os.makedirs(attachment_dir, exist_ok=True)
    return attachment_dir


@send_bp.route("/upload-attachment", methods=["POST"])
@api_login_required
def upload_attachment():
    """Upload a file attachment and return its temp file path."""
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "文件名为空"}), 400

    attachment_dir = _get_attachment_dir()
    # Use a unique name to avoid collisions
    safe_name = f"{uuid.uuid4().hex[:8]}_{f.filename}"
    filepath = os.path.join(attachment_dir, safe_name)
    f.save(filepath)

    return jsonify({
        "path": filepath,
        "filename": f.filename,
    })


@send_bp.route("/upload-clipboard", methods=["POST"])
@api_login_required
def upload_clipboard():
    """Save a base64-encoded image from clipboard paste and return its temp file path."""
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "缺少图片数据"}), 400

    b64_str = data["image"]
    # Strip data URL prefix if present (e.g. "data:image/png;base64,...")
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]

    try:
        img_data = base64.b64decode(b64_str)
    except Exception:
        return jsonify({"error": "无效的图片数据"}), 400

    attachment_dir = _get_attachment_dir()
    # Determine extension from the data URL or default to png
    ext = "png"
    if data["image"].startswith("data:image/"):
        mime_part = data["image"].split(";")[0]
        ext = mime_part.split("/")[-1] if "/" in mime_part else "png"

    filename = f"clipboard_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(attachment_dir, filename)
    with open(filepath, "wb") as f:
        f.write(img_data)

    return jsonify({
        "path": filepath,
        "filename": filename,
    })


@send_bp.route("/history")
@login_required
def history():
    logs = api.list_send_logs(limit=100)
    return render_template("send/history.html", logs=logs)
