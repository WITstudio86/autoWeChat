from app.extensions import db


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), unique=True, nullable=False)
    ai_api_key = db.Column(db.String(256))
    ai_endpoint = db.Column(db.String(256), default="https://api.openai.com/v1")
    ai_model = db.Column(db.String(50), default="gpt-4o-mini")
    wechat_delay_ms = db.Column(db.Integer, default=2500)

    teacher = db.relationship("Teacher", backref=db.backref("settings", uselist=False))
