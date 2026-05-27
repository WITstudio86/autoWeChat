import platform
import subprocess
import time
import pyperclip

if platform.system() == "Windows":
    import pyautogui


class WeChatSendError(Exception):
    pass


def send_message(contact: str, message: str, delay_ms: int = 2500) -> bool:
    """Send a WeChat message to the specified contact. Returns True on success."""
    sys_name = platform.system()

    if sys_name == "Darwin":
        _mac_send(contact, message, delay_ms)
    elif sys_name == "Windows":
        _windows_send(contact, message, delay_ms)
    else:
        raise WeChatSendError(f"不支持的系统: {sys_name}")

    return True


def _mac_send(contact: str, message: str, delay_ms: int):
    def keystroke(key, with_cmd=False):
        if with_cmd:
            subprocess.call([
                "osascript", "-e",
                f'tell application "System Events" to keystroke "{key}" using command down'
            ])
        else:
            subprocess.call([
                "osascript", "-e",
                f'tell application "System Events" to keystroke "{key}"'
            ])

    def key_code(code):
        subprocess.call([
            "osascript", "-e",
            f'tell application "System Events" to key code {code}'
        ])

    def cmd_enter():
        subprocess.call([
            "osascript", "-e",
            'tell application "System Events" to keystroke return using command down'
        ])

    base_delay = max(delay_ms / 1000.0, 0.5)

    subprocess.call(["open", "-a", "WeChat"])
    time.sleep(max(base_delay * 1.2, 3.0))

    keystroke("f", with_cmd=True)
    time.sleep(base_delay * 0.4)

    pyperclip.copy(contact)
    keystroke("v", with_cmd=True)
    time.sleep(base_delay * 0.4)

    key_code(36)
    time.sleep(base_delay * 0.6)

    pyperclip.copy(message)
    keystroke("v", with_cmd=True)
    time.sleep(base_delay * 0.2)

    cmd_enter()
    time.sleep(base_delay * 0.3)


def _windows_send(contact: str, message: str, delay_ms: int):
    base_delay = max(delay_ms / 1000.0, 0.5)

    subprocess.call(["start", "WeChat"], shell=True)
    time.sleep(max(base_delay * 1.2, 3.0))

    pyautogui.hotkey("ctrl", "f")
    time.sleep(base_delay * 0.4)

    pyperclip.copy(contact)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(base_delay * 0.4)

    pyautogui.press("enter")
    time.sleep(base_delay * 0.6)

    pyperclip.copy(message)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(base_delay * 0.2)

    pyautogui.hotkey("ctrl", "enter")
    time.sleep(base_delay * 0.3)
