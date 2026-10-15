"""Bounded test2 session with private mouse input and reversible diagnostic DLL.

Backups are on disk before installation. Original DLL/configs are restored on
ordinary errors; the recovery manifest also supports recovery after interruption.
"""
import argparse
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import display
from trace_engine import ROOT

TEST2_SHA = "56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wrapper", type=Path)
    ap.add_argument("--trace", action="store_true",
                    help="Collect hardware call trace; debugger overhead invalidates FPS timing")
    ap.add_argument("--watch-unit0-state", action="store_true")
    ap.add_argument("--watch-unit0-render", action="store_true")
    ap.add_argument("--trace-site", action="append", default=[])
    ap.add_argument("--watch-surface-pixel", nargs=2, type=int, metavar=("X", "Y"))
    ap.add_argument("--watch-memory", type=lambda value: int(value, 0))
    ap.add_argument("--repath-patch", action="store_true",
                    help="Apply temporary known-build experimental in-memory fast path")
    ap.add_argument("--unit-blob", action="store_true")
    ap.add_argument("--motion-blob", action="store_true")
    ap.add_argument("--snapshots", action="store_true",
                    help="Save selected game-surface PNGs under modernization/logs/snapshots")
    ap.add_argument("--repath-trial", type=Path)
    ap.add_argument("--pre-trial", type=Path, action="append", default=[],
                    help="Inject hash-gated timing modules before a combined renderer")
    ap.add_argument("--extra-trial", type=Path, action="append", default=[],
                    help="Inject additional hash-gated disposable modules after the primary trial")
    ap.add_argument("--force-repath-rollback", action="store_true",
                    help="Force trial rollback after native segment start in owned process")
    ap.add_argument("--disable-trial-redirect", action="store_true",
                    help="Keep trial draw logging but use native delayed movement")
    ap.add_argument("--boundary-route-patch", action="store_true")
    ap.add_argument("--disable-frame-skip", action="store_true")
    ap.add_argument("--light-wrapper", action="store_true", help="Disable costly full-image diagnostic hashes")
    ap.add_argument("--offscreen", action="store_true", help="Keep the owned test window outside the desktop during private-input trials")
    ap.add_argument("--direct-route-patch", action="store_true",
                    help="Experimental in-memory unit0 direct-route detour")
    ap.add_argument("--direct-route-all-orders", action="store_true",
                    help="Experimental synchronous route dispatch for unit0 on either branch")
    ap.add_argument("--route-limit", type=int,
                    help="Experimental in-memory MaxNodesForRouteFinding override")
    ap.add_argument("--logic-fps", type=int, choices=(20, 30),
                    help="Temporarily test a known logic FPS preference")
    ap.add_argument("--repeat-cycles", type=int, default=0,
                    help="Alternate up/down cliff orders this many times")
    ap.add_argument("--repeat-interval", type=float, default=1.5)
    ap.add_argument("--order-point", nargs=2, type=int, action="append")
    ap.add_argument("--warmup-order", nargs=2, type=int)
    ap.add_argument("--warmup-seconds", type=float, default=0)
    ap.add_argument("--manual-hold", action="store_true",
                    help="Leave the visible test2 game open for user-controlled trial until it exits")
    ap.add_argument("--escape-after-movement", action="store_true",
                    help="Post Escape in the owned game and sample runtime state before cleanup")
    args = ap.parse_args()
    display.verify_baseline()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                  wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_size_t,
                                          ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL

    def runtime_state(pid):
        handle = kernel.OpenProcess(0x1010, False, pid)  # query and read only
        if not handle:
            raise RuntimeError(f"Cannot read owned game process {pid}")
        fields = {"logic_fps": 0x6de6fd, "frame_skip_max": 0x5e1418,
                  "game_time": 0x6c4830, "route_limit": 0x5e174c,
                  "player_count": 0x6e1f0c, "scene_mode": 0x6e1f68,
                  "surface_width": 0x6a49f0, "surface_height": 0x6a49f4,
                  "timer_active": 0x6c5038}
        try:
            result = {}
            for name, address in fields.items():
                value = ctypes.c_uint32()
                count = ctypes.c_size_t()
                if not kernel.ReadProcessMemory(handle, ctypes.c_void_p(address),
                                                ctypes.byref(value), ctypes.sizeof(value),
                                                ctypes.byref(count)) or count.value != 4:
                    raise RuntimeError(f"Cannot read {name} at {address:#x}")
                result[name] = value.value
            return result
        finally:
            kernel.CloseHandle(handle)
    process_rows = csv.reader(subprocess.check_output(
        ["tasklist", "/FO", "CSV", "/NH"], text=True).splitlines())
    active_games = []
    for row in process_rows:
        if not row or not row[0].lower().startswith("chaos") or not row[0].lower().endswith(".exe"):
            continue
        handle = kernel.OpenProcess(0x1000, False, int(row[1]))
        if not handle:
            raise RuntimeError(f"Cannot identify game process {row[1]}")
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(buffer))
            if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
                raise RuntimeError(f"Cannot identify game process {row[1]}")
            if Path(buffer.value).resolve().parent == ROOT.resolve():
                active_games.append(f"{row[0]} ({row[1]})")
        finally:
            kernel.CloseHandle(handle)
    if active_games:
        raise SystemExit(f"A game process is active: {', '.join(active_games)}")
    saves = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "Save").glob("*.sav")}
    if saves.get(ROOT / "Save/test2.sav") != TEST2_SHA:
        raise SystemExit("test2 fixture version changed")
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.restype = wintypes.HWND
    def foreground():
        handle = user.GetForegroundWindow()
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(pid))
        return {"hwnd": handle, "pid": pid.value}
    user.SetForegroundWindow.argtypes = [wintypes.HWND]
    user.SetForegroundWindow.restype = wintypes.BOOL
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    user.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user.AttachThreadInput.restype = wintypes.BOOL
    user.IsWindow.argtypes = [wintypes.HWND]
    user.IsWindow.restype = wintypes.BOOL
    user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.GetClientRect.restype = wintypes.BOOL
    files = [ROOT / "ddraw.dll", ROOT / "ddraw.ini", ROOT / "CFG/prefs.cfg"]
    originals = {p: p.read_bytes() for p in files}
    backup_dir = ROOT / "modernization/logs" / f"background-backup-{time.time_ns()}"
    backup_dir.mkdir(parents=True)
    entries = []
    for index, (path, data) in enumerate(originals.items()):
        backup = backup_dir / f"{index}-{path.name}"
        backup.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        if hashlib.sha256(backup.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Backup hash mismatch")
        entries.append({"path": str(path), "backup": str(backup), "sha256": digest})
    (backup_dir / "recovery.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    proc = None
    logs = [ROOT / "modernization/logs/wrapper-probe.csv",
            ROOT / "modernization/logs/frame-hash.csv",
            ROOT / "modernization/logs/surface-calls.csv",
            ROOT / "modernization/logs/surface-blt-hashes.csv",
            ROOT / "modernization/logs/repath-trial.csv"]
    for path in logs:
        if path.exists():
            path.rename(path.with_name(f"{path.stem}-previous-{time.time_ns()}{path.suffix}"))
    states = [{"stage": "before_launch", **foreground()}]
    runtime_states = []
    failure = None
    try:
        files[0].write_bytes(args.wrapper.read_bytes())
        ini_values = {"windowed": "true", "noactivateapp": "false" if args.manual_hold else "true",
                      "nonexclusive": "true"}
        if args.snapshots:
            ini_values["screenshotdir"] = ".\\modernization\\logs\\snapshots\\"
        ini = display.update_ddraw(originals[files[1]].decode("cp1252"), ini_values)
        files[1].write_bytes(ini.encode("cp1252"))
        if args.logic_fps is not None:
            fps_key=b"MaxFramesPerSec=30"
            if originals[files[2]].count(fps_key)!=1:
                raise RuntimeError("Installed 30-FPS preference gate failed")
            files[2].write_bytes(originals[files[2]].replace(
                fps_key, f"MaxFramesPerSec={args.logic_fps}".encode("ascii")))
        environment = dict(os.environ, MM_PROBE_BACKGROUND_INPUT="1")
        if args.force_repath_rollback:
            if not args.repath_trial:
                raise RuntimeError("Forced rollback needs the trial DLL")
            environment["MM_PROBE_FORCE_ROLLBACK"] = "1"
        if args.disable_trial_redirect:
            if not args.repath_trial:
                raise RuntimeError("Native draw baseline needs the trial logging DLL")
        elif args.repath_trial:
            environment["MM_PROBE_ENABLE_REDIRECT"] = "1"
        if args.light_wrapper:
            environment["MM_PROBE_LIGHT"] = "1"
        startup = subprocess.STARTUPINFO()
        startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 4  # SW_SHOWNOACTIVATE
        proc = subprocess.Popen([str(ROOT / "Chaos.exe")], cwd=ROOT,
                                env=environment, startupinfo=startup)
        time.sleep(4)
        states.append({"stage": "after_launch", **foreground()})
        if args.offscreen:
            callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
            user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
            def move_owned_window(hwnd, _):
                candidate = wintypes.DWORD()
                user.GetWindowThreadProcessId(hwnd, ctypes.byref(candidate))
                if candidate.value == proc.pid:
                    user.SetWindowPos(hwnd, None, -30000, -30000, 0, 0, 0x0015)
                return True
            user.EnumWindows(callback_type(move_owned_window), 0)
        if states[-1]["pid"] == proc.pid and states[0]["hwnd"]:
            user.SetForegroundWindow(states[0]["hwnd"])
            time.sleep(0.2)
            if foreground()["pid"] == proc.pid and user.IsWindow(states[0]["hwnd"]):
                game_tid = user.GetWindowThreadProcessId(states[-1]["hwnd"], None)
                target_tid = user.GetWindowThreadProcessId(states[0]["hwnd"], None)
                if game_tid and target_tid and game_tid != target_tid:
                    if user.AttachThreadInput(game_tid, target_tid, True):
                        try:
                            user.SetForegroundWindow(states[0]["hwnd"])
                        finally:
                            user.AttachThreadInput(game_tid, target_tid, False)
                    time.sleep(0.2)
        states.append({"stage": "after_focus_restore_attempt", **foreground()})
        def helper(*args):
            command = [sys.executable, str(ROOT / "modernization/tools/game_window.py"),
                       str(proc.pid), *map(str, args), "--virtual-mouse", "--input-only"]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            return json.loads(result.stdout)
        menu_ack = helper("--click", 400, 380)
        print(json.dumps({"menu_input": menu_ack}), flush=True)
        time.sleep(1.5)
        # The wrapper sometimes exposes a transient 774x529 client after
        # startup; wait for the game's 800x600 menu before fixed load clicks.
        size_deadline = time.monotonic() + 10
        while True:
            client = wintypes.RECT()
            if not user.IsWindow(menu_ack["game_window"]) or not user.GetClientRect(menu_ack["game_window"], ctypes.byref(client)):
                raise RuntimeError("Game window closed before load")
            if client.right >= 800 and client.bottom >= 600:
                break
            if time.monotonic() >= size_deadline:
                raise RuntimeError(f"Game menu client stayed {client.right}x{client.bottom}")
            time.sleep(0.2)
        print(json.dumps({"load_input": helper("--click", 140, 555)}), flush=True)
        time.sleep(4)
        states.append({"stage": "after_load", **foreground()})
        if states[-1]["pid"] == proc.pid and states[0]["hwnd"]:
            # An offscreen window can still own keyboard focus. Briefly hide
            # it before restoring the prior foreground window; then reshow
            # without activation so all later clicks use the private channel.
            game_hwnd = states[-1]["hwnd"]
            if user.IsWindow(game_hwnd):
                user.ShowWindow(game_hwnd, 0)  # SW_HIDE
                user.SetForegroundWindow(states[0]["hwnd"])
                user.ShowWindow(game_hwnd, 4)  # SW_SHOWNOACTIVATE
                time.sleep(0.2)
            states.append({"stage": "after_load_focus_restore", **foreground()})
        # Confirm the distinctive test2 unit table before fixed scene clicks.
        result = subprocess.run([sys.executable, str(ROOT / "modernization/tools/telemetry.py"),
                                 str(proc.pid), "--seconds", "0.2", "--units"],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        data, _ = json.JSONDecoder().raw_decode(result.stdout)
        if data["unit_candidates"]["first"][0][1:4] != [66, 48, 6] or data["first_values"]["unit_table_count_candidate"] != 125:
            raise RuntimeError("test2 memory gate failed; fixed-point movement refused")
        if args.repath_patch:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/patch_repath_live.py"),
                            str(proc.pid)], cwd=ROOT, check=True)
        if args.boundary_route_patch:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/patch_boundary_route_live.py"),
                            str(proc.pid)], cwd=ROOT, check=True)
        if args.disable_frame_skip:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/patch_frame_skip_live.py"),
                            str(proc.pid)], cwd=ROOT, check=True)
        if args.direct_route_patch or args.direct_route_all_orders:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/patch_direct_route_live.py"),
                            str(proc.pid), *(["--all-orders"] if args.direct_route_all_orders else [])],
                           cwd=ROOT, check=True)
        if args.route_limit is not None:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/patch_route_limit_live.py"),
                            str(proc.pid), str(args.route_limit)], cwd=ROOT, check=True)
        for dll in args.pre_trial:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/inject_repath_trial.py"),
                            str(proc.pid), str(dll)], cwd=ROOT, check=True)
        if args.repath_trial:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/inject_repath_trial.py"),
                            str(proc.pid), str(args.repath_trial)], cwd=ROOT, check=True)
        for dll in args.extra_trial:
            subprocess.run([sys.executable, str(ROOT / "modernization/tools/inject_repath_trial.py"),
                            str(proc.pid), str(dll)], cwd=ROOT, check=True)
        runtime_states.append({"stage": "after_injection", **runtime_state(proc.pid)})
        if args.manual_hold:
            user.ShowWindow(menu_ack["game_window"], 5)  # SW_SHOW
            user.SetForegroundWindow(menu_ack["game_window"])
            print(json.dumps({"manual_ready": True, "game_pid": proc.pid,
                              "trial_dll": str(args.repath_trial) if args.repath_trial else None,
                              "test2_memory_gate": True,
                              "foreground": foreground()}), flush=True)
            proc.wait()
            states.append({"stage": "after_manual_trial", **foreground()})
        elif args.repeat_cycles:
            command = [sys.executable, str(ROOT / "modernization/tools/probe_repath_repeat.py"),
                       str(proc.pid), "--cycles", str(args.repeat_cycles),
                       "--interval", str(args.repeat_interval),
                       *(["--unit-blob"] if args.unit_blob else []),
                       *(["--motion-blob"] if args.motion_blob else []),
                       *(["--snapshots"] if args.snapshots else []),
                       *(["--trace"] if args.trace else []),
                       *(["--watch-unit0-state"] if args.watch_unit0_state else []),
                       *(["--watch-unit0-render"] if args.watch_unit0_render else []),
                       *(item for site in args.trace_site for item in ("--trace-site", site))]
            if args.watch_surface_pixel:
                command.extend(("--watch-surface-pixel", *map(str, args.watch_surface_pixel)))
            for point in args.order_point or []:
                command.extend(("--order-point", *map(str, point)))
            if args.warmup_order:
                command.extend(("--warmup-order", *map(str,args.warmup_order),
                                "--warmup-seconds",str(args.warmup_seconds)))
            if args.watch_memory is not None:
                command.extend(("--watch-memory", hex(args.watch_memory)))
        else:
            command = [sys.executable, str(ROOT / "modernization/tools/probe_repath.py"),
                                 str(proc.pid), "--select", "400", "295", "--first", "455", "350",
                                 "--second", "400", "100", "--delay", "0.35", "--seconds", "6",
                                 "--virtual-mouse", *(["--trace"] if args.trace else []),
                                 *(["--unit-blob"] if args.unit_blob else []),
                                 *(item for site in args.trace_site for item in ("--trace-site", site))]
        if not args.manual_hold:
            result = subprocess.run(command,
                                    cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            print(result.stdout, flush=True)
            states.append({"stage": "after_movement", **foreground()})
            runtime_states.append({"stage": "after_movement", **runtime_state(proc.pid)})
            if args.escape_after_movement:
                helper("--key", "escape")
                time.sleep(1)
                states.append({"stage": "after_escape", **foreground()})
                runtime_states.append({"stage": "after_escape", **runtime_state(proc.pid)})
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        restore_errors = []
        for path, data in originals.items():
            try:
                path.write_bytes(data)
                if path.read_bytes() != data:
                    raise RuntimeError("Restore verification failed")
            except Exception as exc:
                restore_errors.append(f"{path}: {exc}")
        changed_saves = [str(p) for p, digest in saves.items()
                         if hashlib.sha256(p.read_bytes()).hexdigest() != digest]
        report = {"foreground_states": states, "failure": failure,
                  "runtime_states": runtime_states,
                  "temporary_repath_patch": args.repath_patch,
                  "temporary_boundary_route_patch": args.boundary_route_patch,
                  "temporary_disable_frame_skip": args.disable_frame_skip,
                  "light_wrapper": args.light_wrapper,
                  "offscreen": args.offscreen,
                  "escape_after_movement": args.escape_after_movement,
                  "temporary_repath_trial": str(args.repath_trial) if args.repath_trial else None,
                  "temporary_pre_trials": list(map(str, args.pre_trial)),
                  "temporary_extra_trials": list(map(str, args.extra_trial)),
                  "temporary_direct_route_patch": args.direct_route_patch,
                  "temporary_direct_route_all_orders": args.direct_route_all_orders,
                  "temporary_route_limit": args.route_limit,
                  "game_pid": proc.pid if proc else None, "restore_errors": restore_errors,
                  "changed_saves": changed_saves, "recovery_manifest": str(backup_dir / "recovery.json")}
        report["wrapper_event_log"] = str(logs[0]) if logs[0].exists() else None
        report["frame_hash_log"] = str(logs[1]) if logs[1].exists() else None
        report["surface_calls_log"] = str(logs[2]) if logs[2].exists() else None
        report["surface_blt_hashes_log"] = str(logs[3]) if logs[3].exists() else None
        (backup_dir / "session.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        if failure or restore_errors or changed_saves:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
