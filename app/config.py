import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    SECRET_KEY = os.environ.get("SECRET_KEY", "autowechat-dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(INSTANCE_DIR, 'autowechat.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session 配置：确保 fetch 请求携带 cookie
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    # DeepSeek AI 全局配置
    AI_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-2f4733c9ad11405eb7d67962d1219bba")
    AI_API_ENDPOINT = "https://api.deepseek.com/v1"
    AI_MODEL = "deepseek-v4-flash"
