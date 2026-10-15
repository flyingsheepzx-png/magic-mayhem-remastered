"""Run a bounded, background-input HD UI trial in the marked game copy.

This never changes the primary installation. The diagnostic wrapper, settings,
and selected menu image are backed up and restored after the owned process ends.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

LAB_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_TOOLS))
from verify_hd60_runtime import configured_kernel, processes

from PIL import Image, ImageChops, ImageStat
import display
import hd_menu_fit
import hd_ui_fit

ROOT = LAB_TOOLS.parents[1] / "game"
EXE_SHA = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
SURFACE_LAB_SHA = "78eb2b2ea95c5960308c90d22741f0fa438b0d1e04c93804347d425a6c0159fc"
VIEWPORT_RECT_LAB_SHA = "0ce5ae60b3d399ff10632e5755e601afe8fd02f5691d62147615df90a1ea4f52"
HUD_LAB_SHA = "8d350c61d8691c135028db334b7a1e6056341870706e48612c7e0eac2d49b0f0"
BACKGROUND_WRAPPER_SHA = "217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8"
TEST2_SHA = "56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OwnedChild:
    """Expose the hash-gated launcher's owned engine PID to the HD harness."""
    def __init__(self, launcher):
        self.launcher = launcher
        kernel = configured_kernel()
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            matches = [pid for pid, parent, name in processes(kernel)
                       if parent == launcher.pid and name == "chaos-hd60-engine.exe"]
            if matches:
                self.pid = matches[0]
                return
            if launcher.poll() is not None:
                raise RuntimeError(f"Combined launcher exited early: {launcher.returncode}")
            time.sleep(0.2)
        raise RuntimeError("Combined engine child did not start")

    def poll(self):
        return self.launcher.poll()

    def terminate(self):
        kernel = configured_kernel()
        handle = kernel.OpenProcess(0x00100001, 0, self.pid)
        if handle:
            kernel.TerminateProcess(handle, 0)
            kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            kernel.WaitForSingleObject(handle, 5000)
            kernel.CloseHandle(handle)
        if self.launcher.poll() is None:
            self.launcher.terminate()

    def kill(self):
        self.terminate()

    def wait(self, timeout=None):
        return self.launcher.wait(timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--click", nargs=2, type=int, metavar=("X", "Y"),
                        help="optional native game-surface click after startup capture")
    parser.add_argument("--present-2k", action="store_true",
                        help="ask the wrapper for a 1920x1440 output window")
    parser.add_argument("--region-icons-flow", action="store_true",
                        help="inspect Grimoire and character screens from region entry")
    parser.add_argument("--menu-flow", action="store_true",
                        help="visit the fitted options and load-game screens using private input")
    parser.add_argument("--load-test2", action="store_true",
                        help="load the verified test2 save using private background clicks")
    parser.add_argument("--select-unit0", action="store_true",
                        help="after test2 loads, select the player for input baseline")
    parser.add_argument("--edge-scroll-test", action="store_true",
                        help="move private mouse to right edge and sample camera candidate fields")
    parser.add_argument("--input-regression", action="store_true",
                        help="test roof toggle, cursor outer bands and four viewport scroll edges")
    parser.add_argument("--rect-probe", nargs=2, type=int, metavar=("WIDTH", "HEIGHT"),
                        help="temporary memory-only battle rectangle diagnostic")
    parser.add_argument("--trace-geometry", action="store_true",
                        help="log DirectDraw surface creation in a disposable wrapper")
    parser.add_argument("--surface-lab", action="store_true",
                        help="run the opt-in 1120x840 surface-sizing sibling executable")
    parser.add_argument("--viewport-rect-lab", action="store_true",
                        help="run the opt-in surface and battle-rectangle sibling executable")
    parser.add_argument("--band-move-test", action="store_true",
                        help="select unit 0 and right-click terrain in the added right band")
    parser.add_argument("--hud-lab", action="store_true",
                        help="run the expanded viewport with bottom-right HUD anchors")
    parser.add_argument("--hud-portrait-test", action="store_true",
                        help="select the player using the relocated portrait before the band order")
    parser.add_argument("--scan-hud-rects", action="store_true",
                        help="read candidate HUD control rectangles in the isolated test2 process")
    parser.add_argument("--scan-controls", action="store_true",
                        help="read registered mouse control rectangles in the isolated test2 process")
    parser.add_argument("--hud-icon-test", action="store_true",
                        help="identify the remaining round icon by private click after test2 load")
    parser.add_argument("--ramp-repath-test", action="store_true",
                        help="issue rapid alternating slope orders in the combined test2 build")
    args = parser.parse_args()
    expanded = args.surface_lab or args.viewport_rect_lab or args.hud_lab
    if sum((args.surface_lab, args.viewport_rect_lab, args.hud_lab)) > 1:
        parser.error("choose one lab executable")
    if args.load_test2 and args.click:
        parser.error("--load-test2 and --click are mutually exclusive")
    if args.select_unit0 and not args.load_test2:
        parser.error("--select-unit0 requires --load-test2")
    if args.edge_scroll_test and not args.load_test2:
        parser.error("--edge-scroll-test requires --load-test2")
    if args.rect_probe and not args.load_test2:
        parser.error("--rect-probe requires --load-test2")
    if args.band_move_test and not (args.load_test2 and (args.viewport_rect_lab or args.hud_lab)):
        parser.error("--band-move-test requires --load-test2 and a viewport or HUD lab")
    if args.hud_portrait_test and not (args.hud_lab and args.band_move_test):
        parser.error("--hud-portrait-test requires --hud-lab --band-move-test")
    if args.hud_icon_test and not (args.hud_lab and args.load_test2):
        parser.error("--hud-icon-test requires --hud-lab --load-test2")
    if args.ramp_repath_test and not (args.hud_lab and args.load_test2):
        parser.error("--ramp-repath-test requires --hud-lab --load-test2")
    if args.rect_probe and not (800 <= args.rect_probe[0] <= 1120 and
                                600 <= args.rect_probe[1] <= 840):
        parser.error("--rect-probe dimensions must be within 800x600 to 1120x840")
    marker = ROOT / "modernization/assets/hd/HD_LAB.json"
    state = json.loads(marker.read_text(encoding="utf-8-sig"))
    if state.get("kind") != "isolated-hd-game-lab" or Path(state["root"]).resolve() != ROOT:
        raise SystemExit("Refusing to run outside the marked HD game copy")
    if sha(ROOT / "Chaos.exe") != EXE_SHA:
        raise SystemExit("Unknown executable hash")
    executable = ROOT / ("Chaos-HD60-Trial.exe" if args.hud_lab else
                         "Chaos-hd-viewport-rect-lab.exe" if args.viewport_rect_lab else
                         "Chaos-hd-surface-lab.exe" if args.surface_lab else "Chaos.exe")
    if args.surface_lab and sha(executable) != SURFACE_LAB_SHA:
        raise SystemExit("Unknown surface-lab executable hash")
    if args.viewport_rect_lab and sha(executable) != VIEWPORT_RECT_LAB_SHA:
        raise SystemExit("Unknown viewport-rect-lab executable hash")
    if args.hud_lab and sha(executable) != HUD_LAB_SHA:
        raise SystemExit("Unknown HUD-lab executable hash")
    if args.load_test2 and sha(ROOT / "Save/test2.sav") != TEST2_SHA:
        raise SystemExit("Unknown test2 fixture hash")
    diagnostic = ROOT / "modernization/assets/hd/background-noactivate-ddraw.dll"
    if sha(diagnostic) != BACKGROUND_WRAPPER_SHA:
        raise SystemExit("Unknown diagnostic wrapper hash")
    target_dll = ROOT / "ddraw.dll"
    target_ini = ROOT / "ddraw.ini"
    originals = {path: path.read_bytes() for path in (target_dll, target_ini, ROOT / "CFG/prefs.cfg",
                                                        *(ROOT / p for p in hd_menu_fit.FILES))}
    save_hashes = {path: sha(path) for path in (ROOT / "Save").glob("*.sav")}
    geometry_log = ROOT / "modernization/assets/hd/directdraw-geometry.csv"
    geometry_log_offset = geometry_log.stat().st_size if geometry_log.exists() else 0
    run_dir = ROOT / "modernization/assets/hd/background-trials" / str(time.time_ns())
    run_dir.mkdir(parents=True)
    # cnc-ddraw uses a 128-byte filename buffer, so give it a short relative path.
    screenshots = ROOT / "modernization/assets/hd/ss"
    screenshots.mkdir(parents=True, exist_ok=True)
    prior_screenshots = set(screenshots.glob("*.png"))
    recovery = [{"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                 "backup": str(run_dir / ("backup-" + path.name))}
                for path, data in originals.items()]
    for row, data in zip(recovery, originals.values()):
        Path(row["backup"]).write_bytes(data)
    (run_dir / "recovery.json").write_text(json.dumps(recovery, indent=2), encoding="utf-8")
    process = None
    result = {"status": "started", "run_dir": str(run_dir), "input": [], "screenshots": []}
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.restype = wintypes.HWND
    foreground_before_launch = user.GetForegroundWindow()
    result["foreground_before_launch"] = foreground_before_launch
    try:
        if args.hud_lab and not hd_ui_fit.STATE.exists():
            for path, data in zip(hd_menu_fit.FILES, hd_menu_fit.fitted_data()):
                (ROOT / path).write_bytes(data)
        target_dll.write_bytes(diagnostic.read_bytes())
        ini = display.update_ddraw(originals[target_ini].decode("cp1252"), {
            "windowed": "true", "fullscreen": "false", "noactivateapp": "true",
            "nonexclusive": "true", "screenshotdir": ".\\modernization\\assets\\hd\\ss\\",
            "width": "1920" if args.present_2k else "0",
            "height": "1440" if args.present_2k else "0",
        })
        target_ini.write_bytes(ini.encode("cp1252"))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 4  # SW_SHOWNOACTIVATE
        environment = dict(os.environ, MM_PROBE_BACKGROUND_INPUT="1")
        if args.trace_geometry:
            environment["MM_HD_GEOMETRY_LOG"] = "1"
        launcher = subprocess.Popen([str(executable)], cwd=ROOT,
                                    env=environment,
                                    startupinfo=startup)
        process = OwnedChild(launcher) if args.hud_lab else launcher
        result["pid"] = process.pid
        time.sleep(4)
        if process.poll() is not None:
            raise RuntimeError("Game exited before background input handshake")
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        windows = []
        window_handles = []
        window_details = []
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        def title(hwnd):
            buffer = ctypes.create_unicode_buffer(512)
            user.GetWindowTextW(hwnd, buffer, len(buffer))
            return buffer.value
        def owned(hwnd, _):
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == process.pid and user.IsWindowVisible(hwnd):
                rect = wintypes.RECT()
                if user.GetClientRect(hwnd, ctypes.byref(rect)):
                    windows.append([rect.right, rect.bottom])
                    window_handles.append(hwnd)
                    children = []
                    def child(child_hwnd, _):
                        value = title(child_hwnd)
                        if value:
                            children.append(value)
                        return True
                    user.EnumChildWindows(hwnd, callback(child), 0)
                    window_details.append({"client": [rect.right, rect.bottom],
                                           "title": title(hwnd), "child_text": children})
            return True
        user.EnumWindows(callback(owned), 0)
        result["client_sizes"] = windows
        result["windows"] = window_details
        result["foreground_after_launch"] = user.GetForegroundWindow()
        result["startup_focus_stolen"] = user.GetForegroundWindow() in window_handles
        if result["startup_focus_stolen"] and foreground_before_launch:
            user.SetForegroundWindow.argtypes = [wintypes.HWND]
            user.SetForegroundWindow(foreground_before_launch)
            time.sleep(0.2)
            if user.GetForegroundWindow() in window_handles:
                user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
                for hwnd in window_handles:
                    user.ShowWindow(hwnd, 0)  # SW_HIDE
                user.SetForegroundWindow(foreground_before_launch)
                for hwnd in window_handles:
                    user.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
                time.sleep(0.2)
        result["foreground_before_input"] = user.GetForegroundWindow()
        if result["foreground_before_input"] in window_handles:
            raise RuntimeError("Game retained foreground; background trial stopped before input")

        if len(window_handles) != 1:
            raise RuntimeError("Expected one owned game window")
        game_hwnd = window_handles[0]
        def current_game_window() -> int:
            candidates = []
            def match(hwnd, _):
                pid = wintypes.DWORD()
                user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == process.pid and user.IsWindowVisible(hwnd):
                    candidates.append(hwnd)
                return True
            user.EnumWindows(callback(match), 0)
            if len(candidates) != 1:
                raise RuntimeError(f"Expected one current game window, got {candidates}")
            return candidates[0]
        user.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
        channel = user.RegisterWindowMessageW("MagicMayhem.Probe.BackgroundMouse.v1")
        user.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                             wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                                             ctypes.POINTER(ctypes.c_size_t)]
        user.SendMessageTimeoutW.restype = ctypes.c_size_t
        def private_message(message: int, coordinates: int = 0) -> None:
            nonlocal game_hwnd
            game_hwnd = current_game_window()
            ack = ctypes.c_size_t()
            if not user.SendMessageTimeoutW(game_hwnd, channel, message, coordinates,
                                            0x0002, 2000, ctypes.byref(ack)):
                raise ctypes.WinError(ctypes.get_last_error())
            if ack.value != 0x4D4D4247:
                raise RuntimeError(f"Private channel refused {message:#x} on window {game_hwnd:#x}; ack={ack.value:#x}")

        private_message(0)  # protocol handshake
        result["input"].append({"kind": "handshake", "private_channel_acknowledged": True,
                                "foreground": user.GetForegroundWindow()})
        private_message(0x8000 + 77)  # game primary-surface screenshot
        native_width, native_height = ((1120, 840) if expanded
                                       else (800, 600))
        def click(x: int, y: int, button: str = "left") -> None:
            if not (0 <= x < native_width and 0 <= y < native_height):
                raise RuntimeError("Click is outside the native game surface")
            packed = (y << 16) | x
            messages = (0x200, 0x201, 0x202) if button == "left" else (0x200, 0x204, 0x205)
            for message in messages:
                private_message(message, packed)
                # Keep button-down across at least two 30 Hz polling intervals.
                time.sleep(0.08 if message in (0x201, 0x204) else 0.03)
            result["input"].append({"kind": "click", "button": button, "native": [x, y],
                                    "private_channel_acknowledged": True,
                                    "foreground": user.GetForegroundWindow()})
        if args.click:
            click(*args.click)
            time.sleep(1.5)
            private_message(0x8000 + 77)
        if args.region_icons_flow:
            click(560, 462) if args.hud_lab else click(400, 330)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(950, 77) if args.hud_lab else click(680, 55)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            result["region_icons_flow"] = "region entry and Grimoire clicked"
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                                ctypes.c_void_p, ctypes.c_size_t,
                                                ctypes.POINTER(ctypes.c_size_t)]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.OpenProcess(0x0010, False, process.pid)
            try:
                def geometry_value(address):
                    value = ctypes.c_uint32()
                    count = ctypes.c_size_t()
                    if not kernel.ReadProcessMemory(handle, address, ctypes.byref(value), 4,
                                                    ctypes.byref(count)) or count.value != 4:
                        raise ctypes.WinError(ctypes.get_last_error())
                    return value.value
                result["primary_metadata"] = {hex(a): geometry_value(a) for a in
                                              (0x6A49F0, 0x6A49F4, 0x6A49F8)}
            finally:
                kernel.CloseHandle(handle)
        if args.menu_flow:
            if not args.hud_lab:
                raise RuntimeError("Menu flow requires the HD UI sibling")
            click(560, 672)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(900, 770)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(560, 532)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(900, 770)
            time.sleep(1.2)
            click(560, 462)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(850, 750)
            time.sleep(1.2)
            click(560, 602)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(560, 315)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            result["menu_flow"] = "options, load game, region entry, quick-battle menu and first quick-battle destination visited"
        if args.load_test2:
            click(560, 532) if args.hud_lab else click(400, 380)
            time.sleep(1.5)
            private_message(0x8000 + 77)
            click(196, 777) if args.hud_lab and hd_ui_fit.STATE.exists() else click(140, 555)
            time.sleep(4)
            if process.poll() is not None:
                raise RuntimeError("Game exited during test2 load")
            private_message(0x8000 + 77)
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                                  ctypes.c_void_p, ctypes.c_size_t,
                                                  ctypes.POINTER(ctypes.c_size_t)]
            kernel.ReadProcessMemory.restype = wintypes.BOOL
            kernel.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                                   ctypes.c_void_p, ctypes.c_size_t,
                                                   ctypes.POINTER(ctypes.c_size_t)]
            kernel.WriteProcessMemory.restype = wintypes.BOOL
            handle = kernel.OpenProcess(0x1000 | 0x10 | (0x8 | 0x20 if args.rect_probe else 0),
                                        False, process.pid)
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                def read32(address: int) -> int:
                    value = wintypes.DWORD()
                    read = ctypes.c_size_t()
                    if not kernel.ReadProcessMemory(handle, address, ctypes.byref(value), 4,
                                                    ctypes.byref(read)) or read.value != 4:
                        raise ctypes.WinError(ctypes.get_last_error())
                    return value.value
                unit_table = read32(0x6DEF58)
                unit_count = read32(0x6DEF5C)
                unit0 = [read32(unit_table + offset) for offset in (8, 12, 16)]
                scene_rect_pointer = read32(0x6C482C)
                scene_rect = [read32(scene_rect_pointer + offset) for offset in (0, 4, 8, 12)]
                camera_rect = [read32(0x689930 + offset) for offset in (0x11, 0x15, 0x19, 0x1D)]
                camera_size = [read32(0x689930 + offset) for offset in (0x51, 0x55)]
                camera_position = [read32(0x689930 + offset) for offset in (0x39, 0x3D, 0x41, 0x45, 0x49, 0x4D)]
                result["battle_geometry_candidates"] = {
                    "scene_rect_pointer": scene_rect_pointer,
                    "scene_rect": scene_rect,
                    "camera_rect": camera_rect,
                    "camera_size": camera_size,
                    "camera_position": camera_position,
                    "label": "read-only candidates; geometry semantics pending validation",
                }
                result["test2_memory_gate"] = {"unit_count": unit_count,
                                                 "unit0_grid": unit0,
                                                 "passed": unit_count == 125 and unit0 == [66, 48, 6]}
                if not result["test2_memory_gate"]["passed"]:
                    raise RuntimeError("test2 battle memory gate failed")
                if args.hud_lab:
                    result["hud_geometry"] = {
                        "wizard_rect": [read32(0x6C4E40 + offset) for offset in (0x11, 0x15, 0x19, 0x1D)],
                        "spellbox_anchor_x": read32(0x6A2DD0 + 0x1914),
                    }
                if args.scan_hud_rects:
                    matches = []
                    for base in (0x6A2DD0, 0x6C4E40):
                        block = (wintypes.DWORD * 4096)()
                        read = ctypes.c_size_t()
                        if not kernel.ReadProcessMemory(handle, base, ctypes.byref(block),
                                                        ctypes.sizeof(block), ctypes.byref(read)):
                            raise ctypes.WinError(ctypes.get_last_error())
                        for index in range(4093):
                            x0, y0, x1, y1 = block[index:index + 4]
                            if (600 <= x0 <= 690 and 480 <= y0 <= 560 and
                                    x0 < x1 <= x0 + 100 and y0 < y1 <= y0 + 100):
                                matches.append({"address": hex(base + index * 4),
                                                "rect": [x0, y0, x1, y1]})
                    result["hud_rect_candidates"] = matches[:100]
                if args.scan_controls:
                    count = read32(0x642c68)
                    if count > 400:
                        raise RuntimeError(f"Unexpected mouse control count: {count}")
                    controls = []
                    for index in range(count):
                        pointer = read32(0x642034 + index * 4)
                        if not pointer:
                            continue
                        try:
                            rect = [read32(pointer + offset) for offset in (0x11, 0x15, 0x19, 0x1d)]
                            control_vtable = read32(pointer)
                        except OSError:
                            continue
                        if (0 <= rect[0] < rect[2] <= 1120 and
                                0 <= rect[1] < rect[3] <= 840):
                            controls.append({"index": index, "pointer": hex(pointer),
                                             "vtable": hex(control_vtable), "rect": rect})
                    result["mouse_controls"] = controls
                if args.edge_scroll_test:
                    private_message(0x200, (300 << 16) | 795)
                    time.sleep(1)
                    result["edge_scroll_camera_position"] = [
                        read32(0x689930 + offset)
                        for offset in (0x39, 0x3D, 0x41, 0x45, 0x49, 0x4D)]
                    private_message(0x8000 + 77)
                if args.input_regression:
                    def camera():
                        return [read32(0x689930 + offset) for offset in
                                (0x39, 0x3d, 0x41, 0x45, 0x49, 0x4d)]
                    roof_before = read32(0x689995)
                    click(970, 768)
                    time.sleep(0.3)
                    roof_after = read32(0x689995)
                    click(970, 768)
                    time.sleep(0.3)
                    result["roof_toggle"] = {"before": roof_before, "after": roof_after,
                                              "restored": read32(0x689995),
                                              "passed": roof_before != roof_after and
                                              read32(0x689995) == roof_before}
                    cursor_samples = []
                    for x, y in ((900, 420), (560, 650), (1100, 680)):
                        private_message(0x200, (y << 16) | x)
                        time.sleep(0.15)
                        samples = []
                        for _ in range(3):
                            samples.append([read32(va) for va in
                                            (0x641a78, 0x641a7c, 0x641a80, 0x641a84)])
                            time.sleep(0.15)
                        cursor_samples.append({"native": [x, y], "restore_rects": samples})
                    result["cursor_outer_bands"] = cursor_samples
                    scroll = []
                    for label, x, y in (("right", native_width - 1, 420),
                                        ("left", 0, 420), ("bottom", 560, native_height - 1),
                                        ("top", 560, 0)):
                        private_message(0x200, (420 << 16) | 560)
                        time.sleep(0.15)
                        before = camera()
                        for _ in range(20):
                            private_message(0x200, (y << 16) | x)
                            time.sleep(0.05)
                        after = camera()
                        scroll.append({"edge": label, "native": [x, y],
                                       "before": before, "after": after,
                                       "changed": before != after,
                                       "cursor_id": read32(0x5e04c8),
                                       "scroll_direction": read32(0x5e1740),
                                       "scroll_gate": read32(0x6f68d8),
                                       "mouse_queue_index": read32(0x641fbc)})
                        time.sleep(0.2)
                    private_message(0x200, (420 << 16) | 560)
                    result["scroll_edges"] = scroll
                    result["input_regression_passed"] = (result["roof_toggle"]["passed"] and
                        all(row["changed"] and row["scroll_direction"] == expected
                            for row, expected in zip(scroll, (7, 9, 8, 6))))
                    if not result["input_regression_passed"]:
                        raise RuntimeError("Roof or four-edge scroll regression failed")
                    time.sleep(1.1)
                    private_message(0x8000 + 77)
                if args.rect_probe:
                    if scene_rect != [0, 0, 800, 600]:
                        raise RuntimeError("Battle rectangle differs from verified baseline")
                    def write32(address: int, number: int) -> None:
                        value = wintypes.DWORD(number)
                        written = ctypes.c_size_t()
                        if not kernel.WriteProcessMemory(handle, address, ctypes.byref(value), 4,
                                                         ctypes.byref(written)) or written.value != 4:
                            raise ctypes.WinError(ctypes.get_last_error())
                        if read32(address) != number:
                            raise RuntimeError("In-memory rectangle write did not verify")
                    width, height = args.rect_probe
                    write32(scene_rect_pointer + 8, width)
                    write32(scene_rect_pointer + 12, height)
                    result["rect_probe"] = {"requested": [width, height],
                                            "scene_rect_after_write": [
                                                read32(scene_rect_pointer + offset)
                                                for offset in (0, 4, 8, 12)]}
                    time.sleep(0.8)
                    if process.poll() is not None:
                        raise RuntimeError("Game exited after memory-only rectangle probe")
                    private_message(0x8000 + 77)
                    result["rect_probe"]["camera_rect_after_wait"] = [
                        read32(0x689930 + offset) for offset in (0x11, 0x15, 0x19, 0x1D)]
                    write32(scene_rect_pointer + 8, 800)
                    write32(scene_rect_pointer + 12, 600)
                if args.band_move_test:
                    before_selection_files = set(screenshots.glob("*.png"))
                    click(1058, 770) if args.hud_portrait_test else click(560, 415)
                    time.sleep(0.8)
                    private_message(0x8000 + 77)
                    selection_files = set(screenshots.glob("*.png")) - before_selection_files
                    if len(selection_files) != 1:
                        raise RuntimeError("Could not capture selection confirmation")
                    with Image.open(next(iter(selection_files))) as selected:
                        pixels = selected.convert("RGB").load()
                        corners = [(540, 358), (541, 358), (583, 358), (584, 358),
                                   (540, 430), (541, 430), (583, 430), (584, 430)]
                        confirmed = sum(pixels[x, y][0] > 150 and pixels[x, y][1] > 140
                                        and pixels[x, y][2] < 80 for x, y in corners)
                    if confirmed < 6:
                        raise RuntimeError("Player selection corners not confirmed; no order sent")
                    before_move = [read32(unit_table + offset) for offset in (8, 12, 16)]
                    click(1000, 420, "right")
                    time.sleep(5)
                    private_message(0x8000 + 77)
                    result["band_move_test"] = {
                        "target_native": [1000, 420],
                        "outside_800x600_centered_overlap": True,
                        "unit0_before": before_move,
                        "selection_corner_pixels_confirmed": confirmed,
                        "unit0_after": [read32(unit_table + offset) for offset in (8, 12, 16)],
                        "camera_after": [read32(0x689930 + offset)
                                         for offset in (0x39, 0x3D, 0x41, 0x45, 0x49, 0x4D)],
                    }
                if args.ramp_repath_test:
                    before_selection_files = set(screenshots.glob("*.png"))
                    click(560, 415)
                    time.sleep(0.7)
                    private_message(0x8000 + 77)
                    selection_files = set(screenshots.glob("*.png")) - before_selection_files
                    if len(selection_files) != 1:
                        raise RuntimeError("Ramp trial could not capture player selection")
                    with Image.open(next(iter(selection_files))) as selected:
                        pixels = selected.convert("RGB").load()
                        corners = [(540, 358), (541, 358), (583, 358), (584, 358),
                                   (540, 430), (541, 430), (583, 430), (584, 430)]
                        confirmed = sum(pixels[x, y][0] > 150 and pixels[x, y][1] > 140
                                        and pixels[x, y][2] < 80 for x, y in corners)
                    if confirmed < 6:
                        raise RuntimeError("Ramp trial selection gate failed")
                    def world():
                        return [read32(unit_table + offset) for offset in (0x14, 0x18, 0x1c)]
                    samples = [world()]
                    click(560, 215, "right")  # start down the long test2 slope
                    for _ in range(90):
                        time.sleep(0.03)
                        samples.append(world())
                    targets = [(560, 620), (560, 215), (360, 415), (760, 415)] * 5
                    for x, y in targets:
                        click(x, y, "right")
                        for _ in range(13):
                            time.sleep(0.03)
                            samples.append(world())
                    jumps = [max(abs(a[i]-b[i]) for i in range(3))
                             for a, b in zip(samples, samples[1:])]
                    result["ramp_repath_test"] = {
                        "selection_corner_pixels_confirmed": confirmed,
                        "orders": len(targets)+1,
                        "world_samples": len(samples),
                        "max_sampled_component_step": max(jumps),
                        "unit0_after": [read32(unit_table + offset) for offset in (8, 12, 16)],
                    }
                    if max(jumps) > 20:
                        raise RuntimeError("Large sampled world-position jump in ramp trial")
            finally:
                kernel.CloseHandle(handle)
            if args.select_unit0 and not args.band_move_test:
                click(560, 415) if (args.viewport_rect_lab or args.hud_lab) else click(400, 295)
                time.sleep(0.8)
                private_message(0x8000 + 77)
            if args.hud_icon_test:
                click(650, 527)
                time.sleep(1)
                private_message(0x8000 + 77)
        captured = sorted(set(screenshots.glob("*.png")) - prior_screenshots)
        archive = run_dir / "screenshots"
        archive.mkdir()
        result["screenshots"] = []
        for number, path in enumerate(captured):
            destination = archive / ("frame-%02d.png" % number)
            shutil.copy2(path, destination)
            result["screenshots"].append(str(destination))
        result["surface_sizes"] = [list(Image.open(path).size) for path in captured]
        if args.trace_geometry:
            if not geometry_log.exists():
                raise RuntimeError("DirectDraw geometry log was not written")
            with geometry_log.open("rb") as stream:
                stream.seek(geometry_log_offset)
                fragment = stream.read()
            destination = run_dir / "directdraw-geometry.csv"
            destination.write_bytes(fragment)
            result["directdraw_geometry_log"] = str(destination)
            result["directdraw_geometry_rows"] = len(fragment.splitlines())
        expected_surface = [1120, 840] if expanded else [800, 600]
        if args.load_test2 and any(size != expected_surface for size in result["surface_sizes"]):
            raise RuntimeError("Unexpected test2 game surface size")
        if len(captured) >= 2:
            with Image.open(captured[0]) as a, Image.open(captured[-1]) as b:
                delta = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
                result["scene_delta_mean"] = round(sum(ImageStat.Stat(delta).mean) / 3, 3)
        if args.select_unit0 and len(captured) >= 4:
            with Image.open(captured[-2]) as a, Image.open(captured[-1]) as b:
                hud = (600, 460, 800, 600)
                delta = ImageChops.difference(a.convert("RGB").crop(hud),
                                               b.convert("RGB").crop(hud))
                result["selection_hud_delta_mean"] = round(sum(ImageStat.Stat(delta).mean) / 3, 3)
        if not result["screenshots"]:
            raise RuntimeError("Private screenshot was acknowledged but no image was written")
        result["status"] = "completed"
    except Exception as error:  # noqa: BLE001 - preserve diagnostics and restore
        result["status"] = "failed"
        result["error"] = str(error)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for path, data in originals.items():
            for attempt in range(20):
                try:
                    path.write_bytes(data)
                    break
                except PermissionError:
                    if attempt == 19:
                        raise
                    time.sleep(0.25)
        result["restored"] = all(path.read_bytes() == data for path, data in originals.items())
        result["changed_saves"] = [str(path) for path, digest in save_hashes.items()
                                   if not path.exists() or sha(path) != digest]
        if result["changed_saves"]:
            result["status"] = "failed"
            result["error"] = "One or more save files changed during the trial"
        (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" and result["restored"] and not result["changed_saves"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
