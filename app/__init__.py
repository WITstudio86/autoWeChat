import os
from flask import Flask, request, jsonify
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请先登录"
    login_manager.login_message_category = "warning"

    # 对 AJAX 请求返回 JSON 错误而非 HTML 重定向
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.blueprint in ("send", "templates") or _is_ajax():
            return jsonify({"error": "未登录或会话已过期，请刷新页面重新登录"}), 401
        from flask import redirect, url_for, flash
        flash(login_manager.login_message, login_manager.login_message_category)
        return redirect(url_for(login_manager.login_view, next=request.url))

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.courses import courses_bp
    from app.routes.students import students_bp
    from app.routes.templates import templates_bp
    from app.routes.send import send_bp
    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(send_bp)

    from app.models import teacher as _  # noqa
    from app.models import course as _  # noqa
    from app.models import student as _  # noqa
    from app.models import template as _  # noqa
    from app.models import send_log as _  # noqa
    from app.models import settings as _  # noqa

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _is_ajax():
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("HX-Request") == "true"
        or request.headers.get("Accept", "").startswith("application/json")
    )


def _seed_admin():
    from app.models.teacher import Teacher
    if Teacher.query.count() == 0:
        admin = Teacher(
            username="admin",
            display_name="管理员",
            is_admin=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("[初始化] 已创建默认管理员账号: admin / admin123，请尽快修改密码")
