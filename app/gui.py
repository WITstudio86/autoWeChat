import tkinter as tk
from tkinter import scrolledtext, messagebox
import queue
import platform
import subprocess
import sys
import webbrowser


def _mono_font(size=10):
    """Return the best available monospace font for the current OS."""
    if platform.system() == "Darwin":
        return ("Menlo", size)
    return ("Consolas", size)


class LogRedirector:
    """Thread-safe stdout/stderr redirect to a tkinter Text widget."""

    def __init__(self, text_widget, original_stream):
        self.text_widget = text_widget
        self.original = original_stream
        self.queue = queue.Queue()

    def write(self, message):
        if self.original:
            try:
                self.original.write(message)
                self.original.flush()
            except Exception:
                pass
        self.queue.put(message)

    def flush(self):
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass

    def poll(self):
        while True:
            try:
                msg = self.queue.get_nowait()
                self._append(msg)
            except queue.Empty:
                break

    def _append(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


def create_app_window(server_url, on_quit):
    """Create the main tkinter window. Returns (root, log_widget, status_label, out_redir, err_redir)."""
    root = tk.Tk()
    root.title("autoWeChat - 教培机构微信通知助手")
    root.geometry("720x520")
    root.minsize(520, 380)

    # -- Top frame --
    top = tk.Frame(root, padx=14, pady=10)
    top.pack(fill=tk.X)

    status_label = tk.Label(top, text="● 服务启动中...", fg="orange", font=("", 13, "bold"))
    status_label.pack(anchor=tk.W)

    url_label = tk.Label(top, text=f"管理页面: {server_url}", font=("", 11))
    url_label.pack(anchor=tk.W, pady=(6, 2))

    tk.Label(top, text="请在浏览器中打开上述地址进行管理", fg="#666").pack(anchor=tk.W)

    # -- Button bar --
    btn_bar = tk.Frame(root, padx=14)
    btn_bar.pack(fill=tk.X, pady=(0, 8))

    open_btn = tk.Button(
        btn_bar, text="打开管理页面",
        command=lambda: webbrowser.open(server_url),
        bg="#4CAF50", fg="white", font=("", 11),
        padx=18, pady=5, cursor="hand2", relief=tk.FLAT,
    )
    open_btn.pack(side=tk.LEFT, padx=(0, 10))

    quit_btn = tk.Button(
        btn_bar, text="关闭程序",
        command=on_quit,
        bg="#f44336", fg="white", font=("", 11),
        padx=18, pady=5, cursor="hand2", relief=tk.FLAT,
    )
    quit_btn.pack(side=tk.LEFT)

    for btn in (open_btn, quit_btn):
        btn.bind("<Enter>", lambda _, b=btn: b.config(relief=tk.RAISED))
        btn.bind("<Leave>", lambda _, b=btn: b.config(relief=tk.FLAT))

    # -- Log area --
    log_frame = tk.Frame(root, padx=14)
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    tk.Label(log_frame, text="运行日志:", anchor=tk.W, font=("", 10, "bold")).pack(fill=tk.X)

    log_text = scrolledtext.ScrolledText(
        log_frame, wrap=tk.WORD,
        font=_mono_font(10),
        bg="#1e1e1e", fg="#d4d4d4",
        insertbackground="white",
        relief=tk.SUNKEN, borderwidth=1,
    )
    log_text.pack(fill=tk.BOTH, expand=True)
    log_text.config(state=tk.DISABLED)

    out_redir = LogRedirector(log_text, sys.__stdout__)
    err_redir = LogRedirector(log_text, sys.__stderr__)

    root.protocol("WM_DELETE_WINDOW", on_quit)

    return root, log_text, status_label, out_redir, err_redir


def show_permission_guide(root):
    """Show first-launch permission guide dialog on macOS.

    Opens Screen Recording and Accessibility settings pages in sequence.
    No-op on Windows.
    """
    if platform.system() != "Darwin":
        return

    messagebox.showinfo(
        "首次使用 — 权限设置",
        "首次使用需要授予两项系统权限：\n\n"
        "1. 屏幕录制 — 用于发送微信后自动截图\n"
        "2. 辅助功能 — 用于自动操控微信发送消息\n\n"
        "点击「确定」后将依次打开系统设置，\n"
        "请在对应页面中分别勾选 autoWeChat 以授权。",
        parent=root,
    )
    # Open Screen Recording and Accessibility panels
    subprocess.call([
        "open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
    ])
    subprocess.call([
        "open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
    ])


def show_update_dialog(root, version, download_url):
    """Show update available dialog. Returns True if user wants to download."""
    return messagebox.askyesno(
        "发现新版本",
        f"发现新版本 v{version}，是否前往下载？",
        parent=root,
    )
