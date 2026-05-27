from datetime import datetime, timezone
from app.extensions import db


class SendLog(db.Model):
    __tablename__ = "send_logs"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    message_content = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("Teacher", backref="send_logs")
    student = db.relationship("Student", backref="send_logs")
    template = db.relationship("NotificationTemplate", backref="send_logs")
