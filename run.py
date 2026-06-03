import sys
import os
import threading
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _crash_log(msg):
    """Write crash info to a log file on Desktop as last-resort fallback."""
    try:
        log_path = os.path.join(os.path.expanduser("~"), "Desktop", "autoWeChat_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def main():
    try:
        from app import create_app
        from app.gui import create_app_window
    except Exception as e:
        _crash_log(f"Import error: {traceback.format_exc()}")
        _show_fatal_error("导入模块失败", str(e))
        return

    PORT = 5002
    SERVER_URL = f"http://127.0.0.1:{PORT}"

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
        else:
            root.after(200, check_started)

    def poll_logs():
        out_redir.poll()
        err_redir.poll()
        root.after(100, poll_logs)

    root.after(200, check_started)
    root.after(100, poll_logs)

    print(f"autoWeChat 教培机构微信通知助手 v1.0")
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
