"""Targeted Python screenshots and input for this game only; no desktop-wide input."""
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import time
from PIL import ImageGrab

ROOT = (Path(__file__).resolve().parents[2] / "game")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--click", nargs=2, type=int, metavar=("X", "Y"))
    ap.add_argument("--right-click", nargs=2, type=int, metavar=("X", "Y"))
    ap.add_argument("--key", choices=("enter", "escape", "pause"))
    ap.add_argument("--activate-only", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.SetProcessDPIAware()
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.SetForegroundWindow.argtypes = [wintypes.HWND]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    candidates = []
    def enum(hwnd, _):
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == args.pid and user.IsWindowVisible(hwnd):
            candidates.append(hwnd)
        return True
    user.EnumWindows(callback_type(enum), 0)
    if len(candidates) != 1:
        raise SystemExit(f"Expected one game window; found {len(candidates)}")
    hwnd = candidates[0]
    user.SetForegroundWindow(hwnd)
    if args.activate_only:
        # The foreground transition can consume the first mouse click.
        # Keep it separate from any control interaction.
        time.sleep(0.5)
        return
    if args.click and args.right_click:
        raise SystemExit("Choose one mouse action")
    if args.click or args.right_click:
        x, y = args.click or args.right_click
        rect = wintypes.RECT()
        user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user.GetClientRect(hwnd, ctypes.byref(rect))
        if not (0 <= x < rect.right and 0 <= y < rect.bottom):
            raise SystemExit("Click outside game client")
        point = wintypes.POINT(x, y)
        user.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        user.ClientToScreen(hwnd, ctypes.byref(point))
        user.SetCursorPos(point.x, point.y)
        time.sleep(0.08)
        user.mouse_event(0x0002 if args.click else 0x0008, 0, 0, 0, 0)
        time.sleep(0.08)
        user.mouse_event(0x0004 if args.click else 0x0010, 0, 0, 0, 0)
    if args.key:
        key = {"enter": 13, "escape": 27, "pause": 19}[args.key]
        user.PostMessageW(hwnd, 0x100, key, 1)
        time.sleep(0.08)
        user.PostMessageW(hwnd, 0x101, key, 0xC0000001)
    time.sleep(0.5)
    rect = wintypes.RECT()
    if not user.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise SystemExit("Game window closed")
    dest = args.output or ROOT / "modernization" / "logs" / "game-window.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True).save(dest)
    print(dest)

if __name__ == "__main__":
    main()
