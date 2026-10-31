# -*- coding: utf-8 -*-
"""嘎嘎大鱼的手眼最小件 v2：截图 / 移动 / 点击 / 打字(Unicode) / 按键 / 找窗口。
DPI 精确到物理像素，SendInput 结构体按 Windows SDK 对齐（x64 = 40 字节）。"""
import ctypes, ctypes.wintypes as wt, time, sys, os, subprocess

u = ctypes.windll.user32
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: pass

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD)]
class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]
class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _INPUTUNION)]

def _send(inp):
    n = u.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    if n != 1:
        raise OSError("SendInput failed err=%d" % ctypes.get_last_error())
    return n

def screen(): return (u.GetSystemMetrics(0), u.GetSystemMetrics(1))

def shot(path, scale=None):
    from PIL import ImageGrab, Image
    im = ImageGrab.grab(all_screens=True)
    if scale and scale < 1:
        im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
    if path.lower().endswith(".jpg"):
        im.convert("RGB").save(path, quality=72)
    else:
        im.save(path)
    return im.size

def pos():
    p = wt.POINT(); u.GetCursorPos(ctypes.byref(p)); return (p.x, p.y)

def move(x, y):
    u.SetCursorPos(int(x), int(y)); time.sleep(0.04); return pos()

def click(x=None, y=None, button="left"):
    if x is not None: move(x, y)
    down, up = ((0x0002, 0x0004) if button == "left" else (0x0008, 0x0010))
    i = INPUT(type=0); i.mi = MOUSEINPUT(0, 0, 0, down, 0, 0); _send(i)
    time.sleep(0.03)
    i = INPUT(type=0); i.mi = MOUSEINPUT(0, 0, 0, up, 0, 0); _send(i)
    time.sleep(0.12); return pos()

def type_text(text):
    cap = INPUT(type=0)  # reuse buffer
    for ch in text:
        for flags in (0x0004, 0x0004 | 0x0002):
            i = INPUT(type=1); i.ki = KEYBDINPUT(0, ord(ch), flags, 0, 0); _send(i)
        time.sleep(0.006)
    return len(text)

VK = {"enter": 0x0D, "tab": 0x09, "esc": 0x1B, "backspace": 0x08, "space": 0x20,
      "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27, "del": 0x2E, "win": 0x5B}

def key(name):
    parts = name.split("+")
    names = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12}
    if len(parts) == 2:
        mod = names[parts[0]]
        k = VK.get(parts[1]) or ord(parts[1].upper())
        u.keybd_event(mod, 0, 0, 0); u.keybd_event(k, 0, 0, 0)
        time.sleep(0.03)
        u.keybd_event(k, 0, 2, 0); u.keybd_event(mod, 0, 2, 0)
    else:
        v = VK[name]
        u.keybd_event(v, 0, 0, 0); time.sleep(0.02); u.keybd_event(v, 0, 2, 0)
    time.sleep(0.1)

def windows():
    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    out = []
    def cb(h, _):
        if u.IsWindowVisible(h):
            n = u.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n+1); u.GetWindowTextW(h, b, n+1)
                r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r))
                pid = wt.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
                out.append({"hwnd": h, "pid": pid.value, "title": b.value,
                            "rect": [r.left, r.top, r.right, r.bottom]})
        return True
    u.EnumWindows(CB(cb), 0)
    return out

def focus(title_part=None, pid=None):
    hits = [w for w in windows() if (pid and w["pid"] == pid) or (title_part and title_part.lower() in w["title"].lower())]
    if not hits: return None
    h = hits[0]["hwnd"]
    u.ShowWindow(h, 5); u.AllowSetForegroundWindow(0xFFFFFFFF); time.sleep(0.1)
    u.BringWindowToTop(h); u.SetForegroundWindow(h); time.sleep(0.35)
    if u.GetForegroundWindow() != h:
        u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0); time.sleep(0.12)
        u.SetForegroundWindow(h); time.sleep(0.3)
    return hits[0]

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"
    if cmd == "shot": print(shot(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else None))
    elif cmd == "move": print(move(sys.argv[2], sys.argv[3]))
    elif cmd == "click": print(click(sys.argv[2], sys.argv[3]))
    elif cmd == "type": print(type_text(sys.argv[2]))
    elif cmd == "key": print(key(sys.argv[2]))
    elif cmd == "wins":
        for w in windows(): print(w["pid"], w["title"], w["rect"])
    else: print("screen", screen(), "cursor", pos(), "sizeof(INPUT)", ctypes.sizeof(INPUT))