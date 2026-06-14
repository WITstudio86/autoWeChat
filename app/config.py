import os
import sys
import json

INSTANCE_DIR = os.path.join(os.path.expanduser("~"), ".autoWeChat")


def get_server_url():
    """Resolve server URL with priority: local config > env var > default remote."""
    config_file = os.path.join(INSTANCE_DIR, "config.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                local_config = json.load(f)
            url = local_config.get("server_url", "").strip()
            if url:
                return url
    except Exception:
        pass

    env_url = os.environ.get("SERVER_BASE_URL", "").strip()
    if env_url:
        return env_url

    return "https://wechat.zelab.top"


def save_server_url(url):
    """Persist server URL to local config file."""
    config_file = os.path.join(INSTANCE_DIR, "config.json")
    config = {}
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
    except Exception:
        pass
    config["server_url"] = url
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def is_first_run():
    """Return True if the setup wizard has not been completed."""
    config_file = os.path.join(INSTANCE_DIR, "config.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
            return not config.get("setup_complete", False)
    except Exception:
        pass
    return True


def mark_setup_complete():
    """Mark the setup wizard as completed."""
    config_file = os.path.join(INSTANCE_DIR, "config.json")
    config = {}
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
    except Exception:
        pass
    config["setup_complete"] = True
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


class Config:
    # Handle PyInstaller frozen state: sys._MEIPASS is the temp bundle dir
    if getattr(sys, "frozen", False):
        BASE_DIR = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    SECRET_KEY = os.environ.get("SECRET_KEY", "autowechat-dev-secret-key")

    # Remote Node.js server
    SERVER_BASE_URL = get_server_url()

    # Session configuration
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

