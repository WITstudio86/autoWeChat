import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    SECRET_KEY = os.environ.get("SECRET_KEY", "autowechat-dev-secret-key")

    # Remote Node.js server
    SERVER_BASE_URL = os.environ.get("SERVER_BASE_URL", "http://localhost:5001")

    # Session configuration
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    # DeepSeek AI global config (used locally for send flow)
    AI_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-2f4733c9ad11405eb7d67962d1219bba")
    AI_API_ENDPOINT = "https://api.deepseek.com/v1"
    AI_MODEL = "deepseek-v4-flash"
