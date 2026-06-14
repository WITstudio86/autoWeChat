import platform
import subprocess
import time
import os
import pyperclip
from typing import Optional

if platform.system() == "Windows":
    import pyautogui


class WeChatSendError(Exception):
    pass


def _paste_file_mac(file_path: str, base_delay: float, app_name: str = "WeChat"):
    """Copy a file to the clipboard via AppleScript and paste into WeChat."""
    r = subprocess.run(["open", "-a", app_name], capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        raise WeChatSendError(f"无法打开 {app_name}")
    time.sleep(0.3)

    escaped_path = file_path.replace("\\", "\\\\").replace('"', '\\"')
    applescript = f'set the clipboard to (POSIX file "{escaped_path}")'
    result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise WeChatSendError(f"设置剪贴板(文件)失败: {result.stderr.strip()}")
    time.sleep(base_delay * 0.3)

    _osascript('tell application "System Events" to keystroke "v" using command down')
    time.sleep(base_delay * 0.8)


def _paste_file_windows(file_path: str, base_delay: float):
    """Copy a file to the clipboard via PowerShell and paste into WeChat."""
    ps_script = f'Set-Clipboard -Path "{file_path}"'
    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
    time.sleep(base_delay * 0.2)

    pyautogui.hotkey("ctrl", "v")
    time.sleep(base_delay * 0.2)


def send_message(contact: str, message: str, delay_ms: int = 2500,
                 app_name: str = "WeChat", attachments: Optional[list] = None) -> bool:
    """Send a WeChat message to the specified contact, with optional file attachments."""
    sys_name = platform.system()

    if sys_name == "Darwin":
        _mac_send(contact, message, delay_ms, app_name, attachments)
    elif sys_name == "Windows":
        _windows_send(contact, message, delay_ms, app_name, attachments)
    else:
        raise WeChatSendError(f"不支持的系统: {sys_name}")

    return True


def _osascript(script):
    """Run an AppleScript and raise on failure."""
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        err = r.stderr.strip() if r.stderr else f"exit code {r.returncode}"
        if "not allowed to send keystrokes" in err.lower() or "not allowed assistive access" in err.lower():
            raise WeChatSendError("缺少辅助功能权限，请在系统设置 > 隐私与安全性 > 辅助功能中授权")
        raise WeChatSendError(f"AppleScript 执行失败: {err}")
    return r


def _mac_send(contact: str, message: str, delay_ms: int, app_name: str,
              attachments: Optional[list] = None):
    def keystroke(key, with_cmd=False):
        if with_cmd:
            _osascript(f'tell application "System Events" to keystroke "{key}" using command down')
        else:
            _osascript(f'tell application "System Events" to keystroke "{key}"')

    def key_code(code):
        _osascript(f'tell application "System Events" to key code {code}')

    def cmd_enter():
        _osascript('tell application "System Events" to keystroke return using command down')

    base_delay = max(delay_ms / 1000.0, 0.3)

    r = subprocess.run(["open", "-a", app_name], capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        raise WeChatSendError(f"无法打开 {app_name}，请确认微信已安装且路径正确")
    time.sleep(1.0)

    keystroke("f", with_cmd=True)
    time.sleep(base_delay * 0.3)

    pyperclip.copy(contact)
    keystroke("v", with_cmd=True)
    time.sleep(base_delay * 0.3)

    key_code(36)
    time.sleep(base_delay * 0.5)

    pyperclip.copy(message)
    keystroke("v", with_cmd=True)
    time.sleep(base_delay * 0.15)

    # Paste attachments after text, before sending
    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                _paste_file_mac(file_path, base_delay, app_name)
        time.sleep(base_delay * 0.3)

    cmd_enter()
    time.sleep(base_delay * 0.3)


def _windows_send(contact: str, message: str, delay_ms: int, app_name: str,
                  attachments: Optional[list] = None):
    base_delay = max(delay_ms / 1000.0, 0.5)

    subprocess.call(["start", app_name], shell=True)
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

    # Paste attachments after text, before sending
    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                _paste_file_windows(file_path, base_delay)

    pyautogui.hotkey("ctrl", "enter")
    time.sleep(base_delay * 0.3)
