from datetime import datetime, timezone
from app.extensions import db


class NotificationTemplate(db.Model):
    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("Teacher", backref="templates")

    @property
    def preview(self):
        """Return first 80 chars as preview."""
        return self.content[:80] + "..." if len(self.content) > 80 else self.content


AVAILABLE_VARIABLES = {
    "{name}": "学员姓名",
    "{class}": "课程时间（如 周六 8:40-10:10）",
    "{date}": "上课日期（如 2026-05-27）",
    "{weekday}": "中文星期（周一~周日）",
    "{teacher}": "教师姓名",
    "{autocontent}": "课程内容（发送时填写概要，AI 扩展成约200字）",
    "{performance}": "学员表现（发送时填写每个学员的概要，AI 扩展成个性化评语）",
}
