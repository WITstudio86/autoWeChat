from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.course import CourseGroup, Course
from app.models.student import Student
from app.models.template import NotificationTemplate
from app.models.send_log import SendLog

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    student_count = Student.query.filter_by(teacher_id=current_user.id).count()
    group_count = CourseGroup.query.filter_by(teacher_id=current_user.id).count()
    template_count = NotificationTemplate.query.filter_by(teacher_id=current_user.id).count()

    today = date.today()
    week_end = today + timedelta(days=7)
    upcoming_courses = Course.query.filter_by(teacher_id=current_user.id)\
        .filter(Course.status == "upcoming")\
        .filter(Course.date <= week_end)\
        .filter(Course.date >= today)\
        .order_by(Course.date).limit(10).all()

    today_courses = Course.query.filter_by(teacher_id=current_user.id)\
        .filter(Course.date == today).all()

    recent_sends = SendLog.query.filter_by(teacher_id=current_user.id)\
        .order_by(SendLog.sent_at.desc()).limit(5).all()

    month_start = today.replace(day=1)
    monthly_sends = SendLog.query.filter_by(teacher_id=current_user.id)\
        .filter(SendLog.sent_at >= month_start).count()

    return render_template("dashboard.html",
                          student_count=student_count,
                          group_count=group_count,
                          template_count=template_count,
                          upcoming_courses=upcoming_courses,
                          today_courses=today_courses,
                          recent_sends=recent_sends,
                          monthly_sends=monthly_sends)
