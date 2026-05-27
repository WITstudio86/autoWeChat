from datetime import datetime, timezone
from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    parent_wechat = db.Column(db.String(200))
    course_group_id = db.Column(db.Integer, db.ForeignKey("course_groups.id"), nullable=True)
    phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("Teacher", backref="students")
