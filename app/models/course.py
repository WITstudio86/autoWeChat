from datetime import datetime, timezone
from app.extensions import db


class CourseGroup(db.Model):
    __tablename__ = "course_groups"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("Teacher", backref="course_groups")
    courses = db.relationship("Course", backref="group", lazy="dynamic",
                              cascade="all, delete-orphan",
                              order_by="Course.date")
    students = db.relationship("Student", backref="course_group", lazy="dynamic")

    @property
    def student_count(self):
        return self.students.count()

    @property
    def time_display(self):
        return f"{self.day_of_week} {self.start_time}-{self.end_time}"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    course_group_id = db.Column(db.Integer, db.ForeignKey("course_groups.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="upcoming")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("Teacher", backref="courses")

    WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    @property
    def weekday_display(self):
        return self.WEEKDAYS[self.date.weekday()]

    @property
    def status_badge(self):
        badges = {
            "upcoming": "bg-primary",
            "completed": "bg-success",
            "cancelled": "bg-secondary",
        }
        return badges.get(self.status, "bg-light")
