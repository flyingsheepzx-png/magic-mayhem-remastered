"""Run a bounded test-save diagnostic with guaranteed owned-process cleanup.

Installs an instrumented wrapper for this session only. Original preferences and
wrapper are restored byte-for-byte after the test, including on ordinary errors.
"""
import argparse
import csv
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image, ImageChops, ImageStat

ROOT = (Path(__file__).resolve().parents[2] / "game")
TEST_SAVE_SHA256 = "62adbfdbc9cb7402e53a26d2e7964d23d15c8801623116fe7a78437118e8e634"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wrapper", type=Path)
    parser.add_argument("--logic", type=int, choices=(20, 30), default=20)
    parser.add_argument("--seconds", type=float, default=8)
    parser.add_argument("--present60", action="store_true")
    parser.add_argument("--load-only", action="store_true", help="Capture each load stage without counter sampling")
    parser.add_argument("--movement-trial", action="store_true", help="Capture a short, fixed right-click movement trial")
    args = parser.parse_args()
    if args.seconds <= 0 or args.seconds > 60:
        raise SystemExit("Session duration must be 0 < seconds <= 60")
    import display
    display.verify_baseline()
    if subprocess.run(["tasklist", "/FI", "IMAGENAME eq Chaos.exe", "/FO", "CSV"],
                      capture_output=True, text=True).stdout.lower().find('"chaos.exe"') >= 0:
        raise SystemExit("Close the existing game before a diagnostic session")
    fixture = ROOT / "Save" / "test.sav"
    if not fixture.is_file():
        raise SystemExit("Test save is missing")
    before_fixture = hashlib.sha256(fixture.read_bytes()).hexdigest()
    if before_fixture != TEST_SAVE_SHA256:
        raise SystemExit("Test save version changed; refusing the fixed-scene measurement")
    files = [ROOT / "ddraw.dll", ROOT / "ddraw.ini", ROOT / "CFG" / "prefs.cfg"]
    original = {p: p.read_bytes() for p in files}
    manifest = json.loads((ROOT / "modernization" / "baseline" / "manifest.json").read_text(encoding="utf-8"))
    expected_prefs = manifest["files"]["CFG/prefs.cfg"]["sha256"]
    if hashlib.sha256(original[files[2]]).hexdigest() != expected_prefs:
        raise SystemExit("Preferences differ from baseline; refusing temporary logic changes")
    if not args.wrapper.is_file():
        raise SystemExit("Instrumented wrapper does not exist")
    log = ROOT / "modernization" / "logs" / "wrapper-probe.csv"
    log.parent.mkdir(exist_ok=True)
    if log.exists():
        log.rename(log.with_name(f"wrapper-probe-previous-{time.time_ns()}.csv"))
    proc = None
    started = time.monotonic()
    try:
        files[0].write_bytes(args.wrapper.read_bytes())
        baseline_prefs = original[files[2]].decode("ascii")
        if baseline_prefs.count("MaxFramesPerSec=20") != 1:
            raise RuntimeError("Expected one baseline frame setting")
        prefs = baseline_prefs.replace("MaxFramesPerSec=20", f"MaxFramesPerSec={args.logic}")
        files[2].write_bytes(prefs.encode("ascii"))
        if args.present60:
            ini = display.update_ddraw(original[files[1]].decode("cp1252"),
                                      {"maxfps": "60", "minfps": "-1"})
            files[1].write_bytes(ini.encode("cp1252"))
        proc = subprocess.Popen([str(ROOT / "Chaos.exe")], cwd=ROOT)
        time.sleep(2)
        helper = ROOT / "modernization" / "tools" / "game_window.py"
        def run_helper(*options):
            result = subprocess.run([sys.executable, str(helper), str(proc.pid), *map(str, options)],
                                    cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(f"Game window helper failed: {result.stderr or result.stdout}")
            return result
        run_helper("--activate-only")
        time.sleep(0.7)
        def capture(stage):
            target = log.with_name(f"load-{stage}-{time.time_ns()}.png")
            run_helper("--output", target)
            return target
        def image_difference(a, b):
            with Image.open(a) as before, Image.open(b) as after:
                if before.size != after.size:
                    return 255.0
                crop = (80, 100, before.width - 80, before.height - 50)
                diff = ImageChops.difference(before.crop(crop).convert("RGB"),
                                             after.crop(crop).convert("RGB"))
                return sum(ImageStat.Stat(diff).mean) / 3
        def forest_fraction(path):
            # This fixture is a forest map. A parchment menu or loading page
            # cannot be accepted as the gameplay measurement scene.
            with Image.open(path) as shot:
                field = shot.crop((80, 100, shot.width - 80, shot.height - 100)).convert("RGB")
                pixels = field.get_flattened_data()
                return sum(g > r * 1.12 and g > b * 1.12 for r, g, b in pixels) / (field.width * field.height)
        def main_menu_ready(path):
            with Image.open(path) as shot:
                # Four parchment button interiors at 800x600. This rejects
                # the black startup transition and the dark battle map.
                for y in (355, 405, 455, 505):
                    patch = shot.crop((250, y, 290, y + 16)).convert("RGB")
                    red, green, blue = ImageStat.Stat(patch).mean
                    if red < 95 or green < 85 or blue < 65:
                        return False
                return True
        def click(x, y):
            if proc.poll() is not None:
                raise RuntimeError(f"Game exited: {proc.returncode}")
            run_helper("--click", x, y)
        menu = None
        for attempt in range(12):
            candidate = capture(f"startup-{attempt + 1}")
            if main_menu_ready(candidate):
                menu = candidate
                break
            if proc.poll() is not None:
                raise RuntimeError(f"Game exited during startup: {proc.returncode}")
            time.sleep(1)
        if menu is None:
            raise RuntimeError("Main menu did not appear within startup deadline")
        load = None
        for attempt in range(3):
            click(400, 380)
            time.sleep(1.5)
            candidate = capture(f"load-attempt-{attempt + 1}")
            difference = image_difference(menu, candidate)
            print(f"Load menu transition attempt {attempt + 1}: difference={difference:.1f}; {candidate}")
            if difference > 12:
                load = candidate
                break
        if load is None:
            raise RuntimeError("Load menu did not open; inspect captured screenshots")
        click(140, 555)
        time.sleep(5)
        game = capture("game")
        difference = image_difference(load, game)
        green = forest_fraction(game)
        print(f"Save load transition: difference={difference:.1f}, forest_fraction={green:.3f}; {game}")
        if difference <= 12 or green < 0.30:
            raise RuntimeError("Test forest scene did not visibly load; inspect captured screenshots")
        if args.load_only:
            return
        if args.movement_trial:
            click(365, 335)
            time.sleep(0.5)
            selected = capture("selected")
            click(440, 335)
            captures = []
            for second in range(5):
                captures.append(str(capture(f"movement-{args.logic}-{second}")))
                time.sleep(0.8)
            print(json.dumps({"logic_setting": args.logic, "selected_screenshot": str(selected),
                              "screenshots": captures}, indent=2))
            return
        kernel = ctypes.WinDLL("kernel32")
        frequency = ctypes.c_longlong()
        kernel.QueryPerformanceFrequency(ctypes.byref(frequency))
        measurement_start = ctypes.c_longlong()
        kernel.QueryPerformanceCounter(ctypes.byref(measurement_start))
        subprocess.run([sys.executable, str(ROOT / "modernization" / "tools" / "telemetry.py"),
                        str(proc.pid), "--seconds", str(args.seconds)], cwd=ROOT, check=True)
        measurement_end = ctypes.c_longlong()
        kernel.QueryPerformanceCounter(ctypes.byref(measurement_end))
        rows = list(csv.DictReader(log.open(newline=""))) if log.exists() else []
        events = [row for row in rows if measurement_start.value <= int(row["qpc"]) <= measurement_end.value]
        summary = {"logic_setting": args.logic, "force_present60": args.present60,
                   "fixture_sha256": before_fixture,
                   "measurement_seconds": (measurement_end.value - measurement_start.value) / frequency.value,
                   "surface_upload_events": sum(row["event"] == "U" for row in events),
                   "presentation_attempt_events": sum(row["event"] == "P" for row in events),
                   "unique_visual_frames_measured": False,
                   "wrapper_sha256": hashlib.sha256(args.wrapper.read_bytes()).hexdigest()}
        dest = log.with_name(f"session-{args.logic}-{'present60' if args.present60 else 'default'}-{time.time_ns()}.json")
        dest.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        for path, data in original.items():
            for attempt in range(10):
                try:
                    path.write_bytes(data)
                    break
                except PermissionError:
                    if attempt == 9:
                        raise
                    time.sleep(0.3)
        if hashlib.sha256(fixture.read_bytes()).hexdigest() != before_fixture:
            raise RuntimeError("Test save changed during the diagnostic session")
        print(f"Restored community files; session {time.monotonic() - started:.1f}s")

if __name__ == "__main__":
    main()
