import platform
import subprocess
import time
import pyperclip
import tkinter as tk
from tkinter import scrolledtext
import sys
import threading

# =========================
# 日志重定向
# =========================
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)

    def flush(self):
        pass

# =========================
# 核心发送功能
# =========================
def send_wechat(contact, message, log_callback):
    def log(text):
        log_callback(text + "\n")

    log("🚀 微信快速发送工具启动")

    try:
        sys = platform.system()
        
        if sys == "Darwin":  # macOS
            log("macOS：启动微信...")
            subprocess.call(["open", "-a", "WeChat"])
            time.sleep(2.5)

            def key(code):
                subprocess.call(["osascript", "-e", f'tell application "System Events" to {code}'])

            log("搜索联系人...")
            key('keystroke "f" using command down')
            time.sleep(0.8)
            
            pyperclip.copy(contact)
            key('keystroke "v" using command down')
            time.sleep(1.0)
            key('key code 36')
            
            time.sleep(1.8)
            log("发送消息...")
            pyperclip.copy(message)
            key('keystroke "v" using command down')
            time.sleep(0.6)
            key('keystroke return using command down')
            
            log("✅ 发送成功！")

        elif sys == "Windows":
            import pyautogui
            log("Windows：启动微信...")
            subprocess.call(["start", "WeChat"], shell=True)
            time.sleep(3)

            pyautogui.hotkey("ctrl", "f")
            time.sleep(1)
            pyperclip.copy(contact)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(1.8)

            pyperclip.copy(message)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.6)
            pyautogui.hotkey("ctrl", "enter")
            
            log("✅ 发送成功！")
        else:
            log(f"❌ 不支持的系统: {sys}")

    except Exception as e:
        log(f"❌ 错误: {str(e)}")

# =========================
# 小窗口版本
# =========================
def main():
    root = tk.Tk()
    root.title("微信快速发送")
    root.geometry("280x190")          # ← 你要求的二分之一大小
    root.resizable(False, False)      # 禁止调整大小（小窗口更整洁）
    
    # 始终置顶
    root.attributes('-topmost', True)

    # 标题
    tk.Label(root, text="微信快速发送", font=("微软雅黑", 11, "bold")).pack(pady=4)

    # 日志区域（小窗口优化）
    log_text = scrolledtext.ScrolledText(
        root, 
        font=("Consolas", 9), 
        bg="#1e1e1e", 
        fg="#00ff88",
        height=8,          # 减少行数适应小窗口
        width=38
    )
    log_text.pack(pady=5, padx=8, fill="both", expand=True)

    # 重定向输出
    sys.stdout = TextRedirector(log_text)

    # 自动执行
    def auto_send():
        CONTACT = "晚自习"
        MESSAGE = "你好"
        send_wechat(CONTACT, MESSAGE, lambda t: log_text.insert(tk.END, t) or log_text.see(tk.END))

    threading.Thread(target=auto_send, daemon=True).start()

    print("启动中...\n")

    root.mainloop()

if __name__ == "__main__":
    main()
