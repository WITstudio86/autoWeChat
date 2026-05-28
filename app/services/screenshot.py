from ctypes import (
    CDLL, CFUNCTYPE, POINTER, byref,
    c_bool, c_char_p, c_double, c_int32, c_long, c_longlong,
    c_uint32, c_void_p, create_string_buffer,
)
import ctypes.util
import os
import platform
import subprocess
import time
from PIL import Image

if platform.system() == "Windows":
    import pyautogui


def _get_wechat_window_id(app_name="WeChat"):
    """Get the target app's CGWindowID for the largest layer-0 window.

    Uses ctypes to call CoreGraphics CGWindowListCopyWindowInfo.
    Returns int window ID, or None if the app is not found.
    """
    if platform.system() != "Darwin":
        return None

    try:
        # Load frameworks
        cg_path = ctypes.util.find_library("CoreGraphics")
        if not cg_path:
            cg_path = "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        cg = CDLL(cg_path)

        cf_path = ctypes.util.find_library("CoreFoundation")
        if not cf_path:
            cf_path = "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        cf = CDLL(cf_path)

        # Set up function signatures
        cf.CFArrayGetCount.argtypes = [c_void_p]
        cf.CFArrayGetCount.restype = c_long

        cf.CFArrayGetValueAtIndex.argtypes = [c_void_p, c_long]
        cf.CFArrayGetValueAtIndex.restype = c_void_p

        cf.CFDictionaryGetValue.argtypes = [c_void_p, c_void_p]
        cf.CFDictionaryGetValue.restype = c_void_p

        cf.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
        cf.CFStringCreateWithCString.restype = c_void_p

        cf.CFStringGetCStringPtr.argtypes = [c_void_p, c_uint32]
        cf.CFStringGetCStringPtr.restype = c_char_p

        cf.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
        cf.CFStringGetCString.restype = c_bool

        cf.CFNumberGetValue.argtypes = [c_void_p, c_long, c_void_p]
        cf.CFNumberGetValue.restype = c_bool

        cf.CFRelease.argtypes = [c_void_p]
        cf.CFRelease.restype = None

        # CGWindowListCopyWindowInfo
        cg.CGWindowListCopyWindowInfo.argtypes = [c_uint32, c_uint32]
        cg.CGWindowListCopyWindowInfo.restype = c_void_p

        UTF8 = 0x08000100
        kCGWindowListOptionOnScreenOnly = 1

        def make_cfstr(s):
            return cf.CFStringCreateWithCString(None, s.encode(), UTF8)

        def cfstr_to_py(cfstr):
            if cfstr is None:
                return ""
            ptr = cf.CFStringGetCStringPtr(cfstr, UTF8)
            if ptr:
                return ptr.decode("utf-8")
            buf = create_string_buffer(256)
            if cf.CFStringGetCString(cfstr, buf, 256, UTF8):
                return buf.value.decode("utf-8")
            return ""

        # Get on-screen window list
        win_array = cg.CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, 0)
        if not win_array:
            return None

        count = cf.CFArrayGetCount(win_array)

        key_owner = make_cfstr("kCGWindowOwnerName")
        key_layer = make_cfstr("kCGWindowLayer")
        key_number = make_cfstr("kCGWindowNumber")
        key_bounds = make_cfstr("kCGWindowBounds")

        best_window_id = None
        best_area = 0

        for i in range(count):
            entry = cf.CFArrayGetValueAtIndex(win_array, i)
            if not entry:
                continue

            owner = cf.CFDictionaryGetValue(entry, key_owner)
            owner_name = cfstr_to_py(owner) if owner else ""

            # Match window owner name against configured app name
            if app_name not in owner_name:
                continue

            # Skip non-layer-0 windows (floating panels, menus, etc.)
            layer_ref = cf.CFDictionaryGetValue(entry, key_layer)
            layer = c_longlong(0)
            if layer_ref:
                cf.CFNumberGetValue(layer_ref, 4, byref(layer))  # kCFNumberLongLongType
            if layer.value != 0:
                continue

            # Get window bounds to calculate area
            bounds_ref = cf.CFDictionaryGetValue(entry, key_bounds)
            if not bounds_ref:
                continue

            key_w = make_cfstr("Width")
            key_h = make_cfstr("Height")
            w_ref = cf.CFDictionaryGetValue(bounds_ref, key_w)
            h_ref = cf.CFDictionaryGetValue(bounds_ref, key_h)

            w_val = c_double(0)
            h_val = c_double(0)
            if w_ref:
                cf.CFNumberGetValue(w_ref, 6, byref(w_val))  # kCFNumberFloat64Type
            if h_ref:
                cf.CFNumberGetValue(h_ref, 6, byref(h_val))

            cf.CFRelease(key_w)
            cf.CFRelease(key_h)

            area = w_val.value * h_val.value
            if area > best_area:
                num_ref = cf.CFDictionaryGetValue(entry, key_number)
                if num_ref:
                    win_num = c_int32(0)
                    if cf.CFNumberGetValue(num_ref, 3, byref(win_num)):  # kCFNumberSInt32Type
                        best_window_id = win_num.value
                        best_area = area

        # Cleanup
        cf.CFRelease(win_array)
        cf.CFRelease(key_owner)
        cf.CFRelease(key_layer)
        cf.CFRelease(key_number)
        cf.CFRelease(key_bounds)

        return best_window_id

    except Exception:
        return None


def capture_wechat_window(output_path: str, app_name: str = "WeChat") -> bool:
    """Capture target app window screenshot. Returns True on success."""
    sys_name = platform.system()
    try:
        if sys_name == "Darwin":
            _mac_capture(output_path, app_name)
        elif sys_name == "Windows":
            _windows_capture(output_path)
        else:
            return False
        return os.path.exists(output_path)
    except Exception:
        return False


def _mac_capture(output_path: str, app_name: str = "WeChat"):
    """Capture target app window on macOS.

    Three-tier fallback:
    1. screencapture -l <windowID> — captures window backing store (Stage Manager safe)
    2. AppleScript get bounds + screencapture -R — coordinate-based (original method)
    3. screencapture -x — full screen (last resort)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Method 1: Capture by CGWindowID (works with Stage Manager)
    win_id = _get_wechat_window_id(app_name)
    if win_id is not None:
        rc = subprocess.call(
            ["screencapture", "-x", "-l", str(win_id), output_path],
            timeout=5,
        )
        if rc == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return

    # Method 2: Coordinate-based capture (original approach)
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set frontmost to true
            set winPos to position of window 1
            set winSize to size of window 1
            return (item 1 of winPos) & "," & (item 2 of winPos) & "," & (item 1 of winSize) & "," & (item 2 of winSize)
        end tell
    end tell
    '''
    try:
        result = subprocess.check_output(["osascript", "-e", script], timeout=5).decode().strip()
        x, y, w, h = map(int, result.split(","))
        time.sleep(0.3)
        rc = subprocess.call(
            ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", output_path],
            timeout=5,
        )
        if rc == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return
    except Exception:
        pass

    # Method 3: Full screen fallback
    subprocess.call(["screencapture", "-x", output_path], timeout=5)


def _windows_capture(output_path: str):
    """Capture full screen on Windows."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = pyautogui.screenshot()
    img.save(output_path)


def stitch_images(image_paths: list, output_path: str, max_width: int = 800) -> str:
    """Stitch multiple images vertically into one long image."""
    if not image_paths:
        return ""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    images = []
    for path in image_paths:
        if not os.path.exists(path):
            continue
        img = Image.open(path)
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        images.append(img)

    if not images:
        return ""

    total_height = sum(img.height for img in images)
    stitched = Image.new("RGB", (max_width, total_height))

    y_offset = 0
    for img in images:
        stitched.paste(img, (0, y_offset))
        y_offset += img.height

    stitched.save(output_path, "PNG")
    return output_path
