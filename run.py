import sys
import os
import threading
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _get_version():
    """Read version from VERSION file bundled with the app."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    version_path = os.path.join(base, "VERSION")
    try:
        with open(version_path, "r") as f:
            return f.read().strip()
    except Exception:
        return "dev"


def _crash_log(msg):
    """Write crash info to a log file on Desktop as last-resort fallback."""
    try:
        log_path = os.path.join(os.path.expanduser("~"), "Desktop", "autoWeChat_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _check_update_thread(root, current_version, server_url):
    """Check for updates in a background thread, show dialog on main thread."""
    try:
        from app.update_checker import check_for_update
    except ImportError:
        return

    import webbrowser as _wb

    def _run():
        try:
            has_update, latest_version, download_url = check_for_update(current_version, server_url)
            if has_update:
                root.after(0, lambda: _on_update_found(latest_version, download_url))
        except Exception:
            pass

    def _on_update_found(latest_version, download_url):
        try:
            from app.gui import show_update_dialog
        except ImportError:
            return
        if show_update_dialog(root, latest_version, download_url):
            _wb.open(download_url + "#download")

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def main():
    try:
        from app import create_app
        from app.gui import create_app_window, show_permission_guide
        from app.config import is_first_run, mark_setup_complete, get_server_url
    except Exception as e:
        _crash_log(f"Import error: {traceback.format_exc()}")
        _show_fatal_error("导入模块失败", str(e))
        return

    VERSION = _get_version()

    PORT = 5002
    SERVER_URL = f"http://127.0.0.1:{PORT}"

    # Remote server URL (Node.js) for update checks
    REMOTE_SERVER_URL = get_server_url()

    try:
        app = create_app()
    except Exception as e:
        _crash_log(f"create_app error: {traceback.format_exc()}")
        _show_fatal_error("创建应用失败", str(e))
        return

    try:
        root, _, status_label, out_redir, err_redir = create_app_window(
            server_url=SERVER_URL,
            on_quit=lambda: root.destroy(),
        )
    except Exception as e:
        _crash_log(f"GUI error: {traceback.format_exc()}")
        _show_fatal_error("创建窗口失败", str(e))
        return

    sys.stdout = out_redir
    sys.stderr = err_redir

    flask_started = threading.Event()

    def run_flask():
        print("Flask 服务启动中...")
        flask_started.set()
        try:
            app.run(debug=False, host="127.0.0.1", port=PORT, use_reloader=False)
        except Exception as e:
            print(f"[ERROR] Flask 服务异常: {e}")
            _crash_log(f"Flask error: {traceback.format_exc()}")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    def check_started():
        if flask_started.is_set():
            status_label.config(text="● 服务运行中", fg="green")
            # First-run permission guide
            if is_first_run():
                mark_setup_complete()
                root.after(500, lambda: show_permission_guide(root))
            # Check for updates in background
            _check_update_thread(root, VERSION, REMOTE_SERVER_URL)
        else:
            root.after(200, check_started)

    def poll_logs():
        out_redir.poll()
        err_redir.poll()
        root.after(100, poll_logs)

    root.after(200, check_started)
    root.after(100, poll_logs)

    print(f"autoWeChat 教培机构微信通知助手 v{VERSION}")
    print(f"管理页面: {SERVER_URL}")
    print(f"点击「关闭程序」按钮退出\n")

    root.mainloop()


def _show_fatal_error(title, message):
    """Show an error dialog — works even if main GUI hasn't started."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(title, f"{title}，请查看桌面上的 autoWeChat_error.log\n\n{message}")
        r.destroy()
    except Exception:
        _crash_log(f"FATAL {title}: {message}")


if __name__ == "__main__":
    main()
