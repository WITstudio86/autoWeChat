from flask import Blueprint, render_template
from app.middleware import login_required
from app.api_client import api

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    stats = api.get_stats()
    return render_template("dashboard.html",
                          student_count=stats["student_count"],
                          group_count=stats["group_count"],
                          template_count=stats["template_count"],
                          upcoming_courses=stats["upcoming_courses"],
                          today_courses=stats["today_courses"],
                          recent_sends=stats["recent_sends"],
                          monthly_sends=stats["monthly_sends"])
