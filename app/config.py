import os
import sys


class Config:
    # Handle PyInstaller frozen state: sys._MEIPASS is the temp bundle dir
    if getattr(sys, "frozen", False):
        BASE_DIR = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    INSTANCE_DIR = os.path.join(os.path.expanduser("~"), ".autoWeChat")

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    SECRET_KEY = os.environ.get("SECRET_KEY", "autowechat-dev-secret-key")

    # Remote Node.js server
    SERVER_BASE_URL = os.environ.get("SERVER_BASE_URL", "http://localhost:5001")

    # Session configuration
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

