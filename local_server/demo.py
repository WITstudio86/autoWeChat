import platform
import subprocess
import time
import pyperclip

# Windows 才需要
if platform.system() == "Windows":
    import pyautogui


CONTACT_NAME = "晚自习"
MESSAGE = "你好"


# =========================
# macOS 实现（AppleScript）
# =========================
def mac_send(contact, message):
    def cmd(key):
        subprocess.call([
            "osascript",
            "-e",
            f'tell application "System Events" to keystroke "{key}" using command down'
        ])

    def enter():
        subprocess.call([
            "osascript",
            "-e",
            'tell application "System Events" to key code 36'
        ])

    def cmd_enter():
        subprocess.call([
            "osascript",
            "-e",
            'tell application "System Events" to keystroke return using command down'
        ])

    print("macOS：启动微信")
    subprocess.call(["open", "-a", "WeChat"])
    time.sleep(3)

    print("macOS：搜索联系人")
    cmd("f")
    time.sleep(1)

    pyperclip.copy(contact)
    cmd("v")
    time.sleep(1)

    enter()
    time.sleep(1.5)

    print("macOS：发送消息")
    pyperclip.copy(message)
    cmd("v")
    time.sleep(0.5)

    cmd_enter()


# =========================
# Windows 实现（pyautogui）
# =========================
def windows_send(contact, message):
    print("Windows：启动微信")
    subprocess.call(["start", "WeChat"], shell=True)
    time.sleep(3)

    print("Windows：搜索联系人")
    pyautogui.hotkey("ctrl", "f")
    time.sleep(1)

    pyperclip.copy(contact)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1)

    pyautogui.press("enter")
    time.sleep(1.5)

    print("Windows：发送消息")
    pyperclip.copy(message)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)

    pyautogui.hotkey("ctrl", "enter")


# =========================
# 自动分发
# =========================
def send_wechat(contact, message):
    sys = platform.system()

    if sys == "Darwin":
        mac_send(contact, message)
    elif sys == "Windows":
        windows_send(contact, message)
    else:
        raise Exception(f"不支持的系统: {sys}")


# =========================
# 入口
# =========================
if __name__ == "__main__":
    send_wechat(CONTACT_NAME, MESSAGE)
