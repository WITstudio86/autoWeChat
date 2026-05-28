from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.middleware import login_required, api_login_required
from app.api_client import api
from app.services.message_renderer import preview_message, AVAILABLE_VARIABLES
from app.services.ai_generator import generate_autocontent

templates_bp = Blueprint("templates", __name__, url_prefix="/templates")


@templates_bp.route("/")
@login_required
def list():
    tmpls = api.list_templates()
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

        api.create_template({
            "name": name,
            "content": content,
            "description": description or None,
        })
        flash(f"模板 '{name}' 创建成功", "success")
        return redirect(url_for("templates.list"))

    return render_template("templates/form.html", template=None,
                          variables=AVAILABLE_VARIABLES)


@templates_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    try:
        tmpl = api.get_template(id)
    except Exception:
        flash("模板不存在", "danger")
        return redirect(url_for("templates.list"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        content = request.form.get("content", "").strip()
        description = request.form.get("description", "").strip() or None

        if not name or not content:
            flash("模板名称和内容不能为空", "danger")
            return render_template("templates/form.html", template=tmpl,
                                  variables=AVAILABLE_VARIABLES)

        api.update_template(id, {
            "name": name,
            "content": content,
            "description": description,
        })
        flash(f"模板 '{name}' 已更新", "success")
        return redirect(url_for("templates.list"))

    return render_template("templates/form.html", template=tmpl,
                          variables=AVAILABLE_VARIABLES)


@templates_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    try:
        tmpl = api.get_template(id)
        api.delete_template(id)
        flash(f"模板 '{tmpl['name']}' 已删除", "success")
    except Exception:
        flash("删除失败", "danger")
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
