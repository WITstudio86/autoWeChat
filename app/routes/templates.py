from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.template import NotificationTemplate, AVAILABLE_VARIABLES
from app.services.message_renderer import preview_message
from app.services.ai_generator import generate_autocontent

templates_bp = Blueprint("templates", __name__, url_prefix="/templates")


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "未登录或会话已过期，请刷新页面重新登录"}), 401
        return f(*args, **kwargs)
    return decorated


@templates_bp.route("/")
@login_required
def list():
    tmpls = NotificationTemplate.query.filter_by(teacher_id=current_user.id)\
        .order_by(NotificationTemplate.updated_at.desc()).all()
    return render_template("templates/list.html", templates=tmpls)


@templates_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        content = request.form.get("content", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not content:
            flash("模板名称和内容不能为空", "danger")
            return render_template("templates/form.html", template=None,
                                  variables=AVAILABLE_VARIABLES)

        tmpl = NotificationTemplate(
            teacher_id=current_user.id,
            name=name,
            content=content,
            description=description or None,
        )
        db.session.add(tmpl)
        db.session.commit()
        flash(f"模板 '{name}' 创建成功", "success")
        return redirect(url_for("templates.list"))

    return render_template("templates/form.html", template=None,
                          variables=AVAILABLE_VARIABLES)


@templates_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    tmpl = NotificationTemplate.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()

    if request.method == "POST":
        tmpl.name = request.form.get("name", "").strip()
        tmpl.content = request.form.get("content", "").strip()
        tmpl.description = request.form.get("description", "").strip() or None

        if not tmpl.name or not tmpl.content:
            flash("模板名称和内容不能为空", "danger")
            return render_template("templates/form.html", template=tmpl,
                                  variables=AVAILABLE_VARIABLES)

        db.session.commit()
        flash(f"模板 '{tmpl.name}' 已更新", "success")
        return redirect(url_for("templates.list"))

    return render_template("templates/form.html", template=tmpl,
                          variables=AVAILABLE_VARIABLES)


@templates_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    tmpl = NotificationTemplate.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    db.session.delete(tmpl)
    db.session.commit()
    flash(f"模板 '{tmpl.name}' 已删除", "success")
    return redirect(url_for("templates.list"))


@templates_bp.route("/preview", methods=["POST"])
@api_login_required
def preview():
    content = request.form.get("content", "")
    rendered = preview_message(content)
    return f'<div class="live-preview" style="white-space: pre-wrap;">{rendered}</div>'


@templates_bp.route("/generate-autocontent", methods=["POST"])
@api_login_required
def generate():
    description = request.form.get("description", "").strip()
    if not description:
        return "[请先填写课程内容描述]", 400

    result = generate_autocontent(description)
    return result
