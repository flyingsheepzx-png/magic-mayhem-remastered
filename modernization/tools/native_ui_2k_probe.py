"""Hash-gated 2560x1440 canvas / 1920x1440 UI screen experiment.

This is an isolated engineering probe, not a game release. It starts from the
installed latest wide169 v7 package and never writes to game/ or game-wide169/.
Main menu, Load Game and Battle Options are adapted as bounded samples.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

import capstone
import pefile
from PIL import Image

import wide169_trial
import display
from wide169_install import inventory
from wide169_build import ROOT, sha


OUT = ROOT / "modernization/assets/hd/native-ui-2k-probe"
LAB = OUT / "runtime"
ENGINE = LAB / "Chaos-Wide169-engine.exe"
MENU = Path("Interface/MainScreen/800x600/Main Menu 800-600.JPG")
CFG = Path("Interface/MainScreen/screen (MainMenu).cfg")
QWEN = ROOT / "modernization/assets/hd/pack/Interface/MainScreen/800x600/Main Menu 800-600.png"
LOAD = Path("Interface/LoadGame/800x600/Load Game 800-600.JPG")
LOAD_CFG = Path("Interface/LoadGame/screen (Load Game).cfg")
OPTIONS = Path("Interface/BattleOptionsScreen/800x600/Battle Options Screen 800-600.JPG")
OPTIONS_CFG = Path("Interface/BattleOptionsScreen/screen (Battle Options).cfg")
QUICK = Path("Interface/QuickBattleMainMenu/800x600/Quick Battle Main Menu 800-600.JPG")
QUICK_CFG = Path("Interface/QuickBattleMainMenu/Screen (Quick Battle Main Menu).cfg")
SOURCE_ENGINE_SHA = "1d2df6135238dec69f6ec74280440a06b43c66353c886f42633f4143d710b16f"

# Existing wide169 fields, read at exact virtual addresses. Primary and window
# dimensions include the engine's fixed 160x120 high-resolution offset.
RAW_FIELDS = {
    0x4E4115: (600, 1320), 0x4E4128: (1120, 2400),
    0x4E41B2: (1120, 2400), 0x4E41D1: (600, 1320),
    0x5E1728: (1280, 2560), 0x5E172C: (720, 1440),
}
INSTRUCTION_FIELDS = {
    0x4A7181: (1120, 2400), 0x4A7192: (600, 1320),
    0x4E8FE0: (1120, 2400), 0x4E8FF3: (600, 1320),
    0x4E9089: (1120, 2400), 0x4E909F: (600, 1320),
    0x4E9131: (1120, 2400), 0x4E9142: (600, 1320),
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def prepare() -> None:
    if OUT.exists():
        raise RuntimeError("Probe directory already exists; preserve its evidence")
    latest = json.loads((ROOT / "modernization/current-baseline.json").read_text(encoding="utf-8"))["latest_development"]
    for relative, expected in latest["files"].items():
        if sha((ROOT / relative).read_bytes()) != expected:
            raise RuntimeError("Latest development identity changed: " + relative)
    installed = json.loads((ROOT / "modernization/wide169-installed.json").read_text(encoding="utf-8"))
    package = Path(installed["package"])
    manifest_raw = (package / "manifest.json").read_bytes()
    if digest(manifest_raw) != installed["manifest_sha256"]:
        raise RuntimeError("Package manifest changed")
    manifest = json.loads(manifest_raw)
    if inventory(package / "runtime") != manifest["files"]:
        raise RuntimeError("Immutable package changed")
    if manifest["engine_sha256"] != SOURCE_ENGINE_SHA:
        raise RuntimeError("Unknown latest wide169 engine")
    queue = json.loads((ROOT / "modernization/assets/hd/hd-queue.json").read_text(encoding="utf-8"))
    record = next(row for row in queue["records"] if row["source"] == MENU.as_posix())
    qwen_raw = QWEN.read_bytes()
    qwen_manifest = json.loads(QWEN.with_suffix(".png.json").read_text(encoding="utf-8"))
    if (record["status"] != "done" or digest(qwen_raw) != record["output_sha256"]
            or qwen_manifest["source_sha256"] != record["source_sha256"]):
        raise RuntimeError("Menu Qwen output not verified")
    shutil.copytree(package / "runtime", LAB)
    (OUT / "game").mkdir()
    (LAB / "ss").mkdir(exist_ok=True)
    source = ENGINE.read_bytes()
    if digest(source) != SOURCE_ENGINE_SHA:
        raise RuntimeError("Copied engine hash mismatch")
    pe = pefile.PE(data=source)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    output = bytearray(source)
    changes = []
    for va, (old, new) in RAW_FIELDS.items():
        offset = pe.get_offset_from_rva(va - 0x400000)
        if source[offset:offset + 4] != struct.pack("<I", old):
            raise RuntimeError(f"Unknown raw field at {va:#x}")
        output[offset:offset + 4] = struct.pack("<I", new)
        changes.append({"va": hex(va), "old": old, "new": new})
    for va, (old, new) in INSTRUCTION_FIELDS.items():
        offset = pe.get_offset_from_rva(va - 0x400000)
        ins = next(decoder.disasm(source[offset:offset + 15], va, 1))
        if ins.mnemonic != "add" or ins.imm_size != 4:
            raise RuntimeError(f"Unknown dimension instruction at {va:#x}")
        field = offset + ins.imm_offset
        if source[field:field + 4] != struct.pack("<I", old):
            raise RuntimeError(f"Unknown dimension at {va:#x}")
        output[field:field + 4] = struct.pack("<I", new)
        changes.append({"va": hex(va + ins.imm_offset), "old": old, "new": new})
    ENGINE.write_bytes(output)
    with Image.open(io.BytesIO(qwen_raw)) as opened:
        if opened.size != (1920, 1440) or opened.format != "PNG":
            raise RuntimeError("Wrong Qwen menu size")
        framed = Image.new("RGB", (2560, 1440))
        framed.paste(opened.convert("RGB"), (320, 0))
    buffer = io.BytesIO()
    framed.save(buffer, "JPEG", quality=100, subsampling=0)
    (LAB / MENU).write_bytes(buffer.getvalue())
    cfg = (LAB / CFG).read_bytes()
    def scale_rect(match: re.Match[bytes]) -> bytes:
        values = [int(match[index]) for index in range(2, 6)]
        return match[1] + b",".join(str(value * 2).encode() for value in values)
    scaled, count = re.subn(rb"(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)", scale_rect, cfg)
    if count != 7:
        raise RuntimeError("Unexpected main-menu rectangle count")
    (LAB / CFG).write_bytes(scaled)
    ini = LAB / "ddraw.ini"
    data = ini.read_text(encoding="cp1252")
    import display
    ini.write_text(display.update_ddraw(data, {"width": "2560", "height": "1440", "windowed": "true", "fullscreen": "false", "savesettings": "0", "screenshotdir": ".\\ss\\"}), encoding="cp1252")
    report = {"kind": "menu-only-native-ui-probe", "source_package": str(package),
              "source_package_manifest_sha256": digest(manifest_raw), "source_engine_sha256": digest(source),
              "patched_engine_sha256": digest(output), "qwen_png_sha256": digest(qwen_raw),
              "framed_menu_sha256": digest(buffer.getvalue()), "menu_cfg_sha256": digest(scaled),
              "native_canvas_goal": [2560, 1440], "ui_content_goal": [1920, 1440],
              "changes": changes}
    (OUT / "build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("patched_engine_sha256", "native_canvas_goal", "ui_content_goal")}, indent=2))


class DirectSession(wide169_trial.Session):
    def start(self):
        k = self.k
        if any(name.startswith("chaos") for _, _, name in wide169_trial.processes(k)):
            raise RuntimeError("Another game instance is running")
        build = json.loads((OUT / "build.json").read_text(encoding="utf-8"))
        if digest(ENGINE.read_bytes()) != build["patched_engine_sha256"]:
            raise RuntimeError("Probe engine changed")
        if "chinese_fonts" in build:
            if digest((LAB / "chaos95.dll").read_bytes()) != build["chinese_fonts"]["patched_dll_sha256"]:
                raise RuntimeError("Probe Chinese font DLL changed")
            import hd_font_probe
            hd_font_probe.verify()
        self.before = {str(p): sha(p.read_bytes()) for p in LAB.rglob("*") if p.is_file() and "ss" not in p.relative_to(LAB).parts}
        self.mutable = {p: (p.read_bytes(), p.stat().st_atime_ns, p.stat().st_mtime_ns)
                        for p in (*sorted((LAB / "Save").glob("*")), *sorted((LAB / "CFG").glob("*.cfg")),
                                  LAB / "AI/EXPERIEN.DAT", LAB / "AI/Brain.dat") if p.is_file()}
        wrapper = LAB / "ddraw.dll"
        self.original[wrapper] = wrapper.read_bytes()
        diagnostic = ROOT / "modernization/assets/hd/background-noactivate-ddraw.dll"
        env = dict(os.environ, MM_PROBE_BACKGROUND_INPUT="1")
        if "mixed_rect" in build:
            if build["mixed_rect"]["after_sha256"] != build["patched_engine_sha256"]:
                raise RuntimeError("Mixed rect manifest mismatch")
            diagnostic = OUT / "mixed-ddraw.dll"
            if sha(diagnostic.read_bytes()) != "04a7dc723b26792deda0860fb48d91df79e5fd857f994c1de0d89b6dffccf17c":
                raise RuntimeError("Unknown mixed diagnostic wrapper")
            env["MM_PROBE_MIXED_RENDER"] = "1"
            ini = LAB / "ddraw.ini"
            self.original[ini] = ini.read_bytes()
            data = ini.read_text(encoding="cp1252")
            ini.write_text(display.update_ddraw(data, {"renderer": "direct3d9", "d3d9_filter": "0"}), encoding="cp1252")
        elif sha(diagnostic.read_bytes()) != "217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8":
            raise RuntimeError("Unknown diagnostic wrapper")
        wrapper.write_bytes(diagnostic.read_bytes())
        self.proc = subprocess.Popen([str(ENGINE)], cwd=LAB, env=env)
        self.pid = self.proc.pid
        self.handle = k.OpenProcess(0x1011, False, self.pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        time.sleep(5)
        if self.proc.poll() is not None:
            raise RuntimeError("Probe engine exited during startup")
        self.channel = self.u.RegisterWindowMessageW("MagicMayhem.Probe.BackgroundMouse.v1")
        self.message(0)
        self.result["checks"] = {"surface": [self.i(0x6A49F0), self.i(0x6A49F4)],
                                  "fps_preference": self.i(0x6DE6FD)}
        rect = W.RECT()
        self.u.GetClientRect(self.window(), ctypes.byref(rect))
        self.result["checks"]["output_client"] = [rect.right, rect.bottom]
        self.capture("menu-native")
        return self

    def capture(self, name):
        super().capture(name)
        with Image.open(self.run / (name + ".png")) as opened:
            if opened.size != (2560, 1440):
                raise RuntimeError("Unexpected native capture geometry")
            rgb = opened.convert("RGB")
            bars = list(rgb.crop((0, 0, 320, 1440)).get_flattened_data())
            bars += list(rgb.crop((2240, 0, 2560, 1440)).get_flattened_data())
            self.result["images"][name]["bar_nonblack_fraction"] = sum(max(pixel) > 8 for pixel in bars) / len(bars)

    def click(self, x, y, right=False):
        if not 0 <= x < 2560 or not 0 <= y < 1440:
            raise ValueError("Native coordinate out of bounds")
        for event in ([0x200, 0x204, 0x205] if right else [0x200, 0x201, 0x202]):
            self.message(event, x, y)
            time.sleep(.09 if event in (0x201, 0x204) else .04)

    def font_metrics(self):
        metrics = {}
        for label, address, height in (("large", 0x6B0400, 64), ("small", 0x656680, 44),
                                       ("tiny", 0x6DF1C0, 30)):
            pointer = self.i(address)
            if not 0x10000 < pointer < 0x7FFFFFFF:
                raise RuntimeError("Invalid font header pointer")
            fields = [self.i(pointer + offset) for offset in (12, 16, 20, 24)]
            if fields[0] != 223 or fields[1] != height or fields[2] + fields[3] != height:
                raise RuntimeError(f"Unexpected native font metrics: {label}/{fields}")
            metrics[label] = {"glyph_count": fields[0], "line_height": fields[1],
                              "ascent": fields[2], "descent": fields[3]}
        return metrics


def probe() -> None:
    if not ENGINE.is_file():
        raise RuntimeError("Run prepare first")
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        check = session.result["checks"]
        controls = [row["rect"] for row in session.controls()]
        expected_button = [680, 744, 1880, 840]
        check["first_menu_button_scaled"] = expected_button in controls
        report = {"checks": check, "capture": str(session.run / "menu-native.png"),
                  "controls": controls}
        (OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


def advance_load() -> None:
    build_path = OUT / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if "load_screen" in build:
        raise RuntimeError("Load screen already staged")
    engine_raw = ENGINE.read_bytes()
    if digest(engine_raw) != build["patched_engine_sha256"]:
        raise RuntimeError("Menu probe engine changed")
    queue = json.loads((ROOT / "modernization/assets/hd/hd-queue.json").read_text(encoding="utf-8"))
    record = next(row for row in queue["records"] if row["source"] == LOAD.as_posix())
    qwen = ROOT / "modernization/assets/hd/pack" / record["output"]
    raw = qwen.read_bytes()
    manifest = json.loads(qwen.with_suffix(".png.json").read_text(encoding="utf-8"))
    if (record["status"] != "done" or digest(raw) != record["output_sha256"]
            or manifest["source_sha256"] != record["source_sha256"]):
        raise RuntimeError("Load Game Qwen output unverified")
    backup = OUT / "before-load"
    backup.mkdir()
    for relative in (Path("Chaos-Wide169-engine.exe"), LOAD, LOAD_CFG):
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAB / relative, destination)
    pe = pefile.PE(data=engine_raw)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    patched = bytearray(engine_raw)
    for va, old, new in ((0x4A9FE2, 1120, 2400), (0x4A9FF3, 600, 1320)):
        offset = pe.get_offset_from_rva(va - 0x400000)
        ins = next(decoder.disasm(engine_raw[offset:offset + 15], va, 1))
        if ins.mnemonic != "add" or ins.imm_size != 4:
            raise RuntimeError("Unknown load surface instruction")
        field = offset + ins.imm_offset
        if engine_raw[field:field + 4] != struct.pack("<I", old):
            raise RuntimeError("Unknown load surface dimensions")
        patched[field:field + 4] = struct.pack("<I", new)
    with Image.open(io.BytesIO(raw)) as opened:
        if opened.format != "PNG" or opened.size != (1920, 1440):
            raise RuntimeError("Wrong Load Game art size")
        framed = Image.new("RGB", (2560, 1440))
        framed.paste(opened.convert("RGB"), (320, 0))
    buffer = io.BytesIO()
    framed.save(buffer, "JPEG", quality=100, subsampling=0)
    cfg = (LAB / LOAD_CFG).read_bytes()
    def scale_rect(match: re.Match[bytes]) -> bytes:
        return match[1] + b",".join(str(int(match[index]) * 2).encode() for index in range(2, 6))
    scaled, count = re.subn(rb"(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)", scale_rect, cfg)
    if count != 6:
        raise RuntimeError("Wrong Load Game rectangle count")
    ENGINE.write_bytes(patched)
    (LAB / LOAD).write_bytes(buffer.getvalue())
    (LAB / LOAD_CFG).write_bytes(scaled)
    build["patched_engine_sha256"] = digest(patched)
    build["load_screen"] = {"qwen_png_sha256": digest(raw), "framed_jpeg_sha256": digest(buffer.getvalue()),
                            "cfg_sha256": digest(scaled), "engine_before_sha256": digest(engine_raw)}
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["load_screen"], indent=2))


def advance_options() -> None:
    build_path = OUT / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if "battle_options" in build:
        raise RuntimeError("Battle Options already staged")
    engine_raw = ENGINE.read_bytes()
    if digest(engine_raw) != build["patched_engine_sha256"]:
        raise RuntimeError("Probe engine changed")
    queue = json.loads((ROOT / "modernization/assets/hd/hd-queue.json").read_text(encoding="utf-8"))
    record = next(row for row in queue["records"] if row["source"] == OPTIONS.as_posix())
    qwen = ROOT / "modernization/assets/hd/pack" / record["output"]
    raw = qwen.read_bytes()
    manifest = json.loads(qwen.with_suffix(".png.json").read_text(encoding="utf-8"))
    if (record["status"] != "done" or digest(raw) != record["output_sha256"]
            or manifest["source_sha256"] != record["source_sha256"]):
        raise RuntimeError("Battle Options Qwen output unverified")
    backup = OUT / "before-options"
    backup.mkdir()
    for relative in (Path("Chaos-Wide169-engine.exe"), OPTIONS, OPTIONS_CFG):
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAB / relative, destination)
    pe = pefile.PE(data=engine_raw)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    patched = bytearray(engine_raw)
    for va, old, new in ((0x4A8ED7, 1120, 2400), (0x4A8EE8, 600, 1320)):
        offset = pe.get_offset_from_rva(va - 0x400000)
        ins = next(decoder.disasm(engine_raw[offset:offset + 15], va, 1))
        if ins.mnemonic != "add" or ins.imm_size != 4:
            raise RuntimeError("Unknown Battle Options surface instruction")
        field = offset + ins.imm_offset
        if engine_raw[field:field + 4] != struct.pack("<I", old):
            raise RuntimeError("Unknown Battle Options surface dimensions")
        patched[field:field + 4] = struct.pack("<I", new)
    with Image.open(io.BytesIO(raw)) as opened:
        if opened.format != "PNG" or opened.size != (1920, 1440):
            raise RuntimeError("Wrong Battle Options art size")
        framed = Image.new("RGB", (2560, 1440))
        framed.paste(opened.convert("RGB"), (320, 0))
    buffer = io.BytesIO()
    framed.save(buffer, "JPEG", quality=100, subsampling=0)
    cfg = (LAB / OPTIONS_CFG).read_bytes()
    def scale_rect(match: re.Match[bytes]) -> bytes:
        return match[1] + b",".join(str(int(match[index]) * 2).encode() for index in range(2, 6))
    scaled, count = re.subn(rb"(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)", scale_rect, cfg)
    if count < 10:
        raise RuntimeError("Too few Battle Options rectangles")
    ENGINE.write_bytes(patched)
    (LAB / OPTIONS).write_bytes(buffer.getvalue())
    (LAB / OPTIONS_CFG).write_bytes(scaled)
    build["patched_engine_sha256"] = digest(patched)
    build["battle_options"] = {"qwen_png_sha256": digest(raw), "framed_jpeg_sha256": digest(buffer.getvalue()),
                                "cfg_sha256": digest(scaled), "engine_before_sha256": digest(engine_raw),
                                "rectangles": count}
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["battle_options"], indent=2))


def advance_quick() -> None:
    """Add the native-size Quick Battle menu to the isolated probe."""
    build_path = OUT / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if "quick_battle" in build:
        raise RuntimeError("Quick Battle already staged")
    engine_raw = ENGINE.read_bytes()
    if digest(engine_raw) != build["patched_engine_sha256"]:
        raise RuntimeError("Probe engine changed")
    queue = json.loads((ROOT / "modernization/assets/hd/hd-queue.json").read_text(encoding="utf-8"))
    record = next(row for row in queue["records"] if row["source"] == QUICK.as_posix())
    qwen = ROOT / "modernization/assets/hd/pack" / record["output"]
    raw = qwen.read_bytes()
    manifest = json.loads(qwen.with_suffix(".png.json").read_text(encoding="utf-8"))
    if (record["status"] != "done" or digest(raw) != record["output_sha256"]
            or manifest["source_sha256"] != record["source_sha256"]):
        raise RuntimeError("Quick Battle Qwen output unverified")
    with Image.open(io.BytesIO(raw)) as opened:
        if opened.format != "PNG" or opened.size != (1920, 1440):
            raise RuntimeError("Wrong Quick Battle art size")
        framed = Image.new("RGB", (2560, 1440))
        framed.paste(opened.convert("RGB"), (320, 0))
    buffer = io.BytesIO()
    framed.save(buffer, "JPEG", quality=100, subsampling=0)
    cfg = (LAB / QUICK_CFG).read_bytes()
    def scale_rect(match: re.Match[bytes]) -> bytes:
        return match[1] + b",".join(str(int(match[index]) * 2).encode() for index in range(2, 6))
    scaled, count = re.subn(rb"(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)", scale_rect, cfg)
    if count != 5:
        raise RuntimeError("Wrong Quick Battle rectangle count")
    pe = pefile.PE(data=engine_raw)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    patched = bytearray(engine_raw)
    edits = []
    for va, old, new in ((0x4A7EAE, 1120, 2400), (0x4A7EBF, 600, 1320)):
        offset = pe.get_offset_from_rva(va - 0x400000)
        ins = next(decoder.disasm(engine_raw[offset:offset + 15], va, 1))
        if ins.mnemonic != "add" or ins.imm_size != 4:
            raise RuntimeError("Unknown Quick Battle surface instruction")
        field = offset + ins.imm_offset
        if engine_raw[field:field + 4] != struct.pack("<I", old):
            raise RuntimeError("Unknown Quick Battle surface dimension")
        patched[field:field + 4] = struct.pack("<I", new)
        edits.append({"va": hex(va + ins.imm_offset), "old": old, "new": new})
    backup = OUT / "before-quick"
    backup.mkdir()
    for relative in (Path("Chaos-Wide169-engine.exe"), QUICK, QUICK_CFG):
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAB / relative, destination)
    ENGINE.write_bytes(patched)
    (LAB / QUICK).write_bytes(buffer.getvalue())
    (LAB / QUICK_CFG).write_bytes(scaled)
    build["patched_engine_sha256"] = digest(patched)
    build["quick_battle"] = {"qwen_png_sha256": digest(raw),
                              "framed_jpeg_sha256": digest(buffer.getvalue()),
                              "cfg_sha256": digest(scaled),
                              "engine_before_sha256": digest(engine_raw),
                              "rectangles": count, "changes": edits}
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["quick_battle"], indent=2))


def follow_quick() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        before = [row["rect"] for row in session.controls()]
        if [680, 984, 1880, 1080] not in before:
            raise RuntimeError("Quick Battle menu button not at scaled native coordinates")
        session.click(1280, 1032)
        time.sleep(.7)
        session.capture("quick-battle-native")
        after = [row["rect"] for row in session.controls()]
        expected = [800, 840, 1760, 960]
        if expected not in after:
            raise RuntimeError("Quick Battle menu did not reach scaled create-game control")
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "fps": session.i(0x6DE6FD), "control_count": len(after),
                  "create_single_player_rect": expected,
                  "capture": str(session.run / "quick-battle-native.png")}
    report["changed_protected"] = session.result["changed_protected"]
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed")
    (OUT / "follow-quick.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def follow_single_setup() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        session.click(1280, 1032)
        time.sleep(.6)
        if [800, 840, 1760, 960] not in [row["rect"] for row in session.controls()]:
            raise RuntimeError("Quick Battle menu not reached")
        session.click(1280, 900)
        time.sleep(.9)
        session.capture("single-player-setup-native")
        controls = [row["rect"] for row in session.controls()]
        expected = ([1280, 1176, 1700, 1260], [1760, 1176, 2180, 1260])
        if not all(rect in controls for rect in expected):
            raise RuntimeError("Single Player setup controls not scaled")
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "fps": session.i(0x6DE6FD), "control_count": len(controls),
                  "cancel_start_rects": expected,
                  "capture": str(session.run / "single-player-setup-native.png"),
                  "bar_nonblack_fraction": session.result["images"]["single-player-setup-native"]["bar_nonblack_fraction"]}
    report["changed_protected"] = session.result["changed_protected"]
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed")
    (OUT / "follow-single-setup.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def follow_map_selection() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        session.click(1280, 1032)
        time.sleep(.55)
        session.click(1280, 900)
        time.sleep(.7)
        if [1280, 240, 1424, 324] not in [row["rect"] for row in session.controls()]:
            raise RuntimeError("Single Player map control not scaled")
        session.click(1352, 282)
        time.sleep(.8)
        session.capture("map-selection-native")
        controls = [row["rect"] for row in session.controls()]
        expected = ([488, 1272, 848, 1392], [1712, 1272, 2072, 1392],
                    [716, 428, 1844, 1030])
        if not all(rect in controls for rect in expected):
            raise RuntimeError("Map Selection controls not scaled")
        session.click(1280, 502)  # Select second visible map row.
        time.sleep(.2)
        session.click(668, 1332)
        time.sleep(.5)
        session.capture("map-selection-return")
        returned = [row["rect"] for row in session.controls()]
        if [1280, 240, 1424, 324] not in returned:
            raise RuntimeError("Map Selection OK did not return to setup")
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "fps": session.i(0x6DE6FD), "control_count": len(controls),
                  "expected_controls": expected,
                  "capture": str(session.run / "map-selection-native.png"),
                  "return_capture": str(session.run / "map-selection-return.png"),
                  "selection_returned": True,
                  "bar_nonblack_fraction": session.result["images"]["map-selection-native"]["bar_nonblack_fraction"]}
    report["changed_protected"] = session.result["changed_protected"]
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed")
    (OUT / "follow-map-selection.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def follow_single_start() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        session.click(1280, 1032)
        time.sleep(.55)
        session.click(1280, 900)
        time.sleep(.7)
        setup = [row["rect"] for row in session.controls()]
        if [1760, 1176, 2180, 1260] not in setup:
            raise RuntimeError("Single Player Start control absent")
        session.click(1970, 1218)
        time.sleep(6)
        if session.proc.poll() is not None:
            raise RuntimeError("Engine exited after Single Player Start")
        session.capture("single-player-start-native")
        after = [row["rect"] for row in session.controls()]
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "fps": session.i(0x6DE6FD),
                  "setup_start_control_gone": [1760, 1176, 2180, 1260] not in after,
                  "controls_after": len(after),
                  "capture": str(session.run / "single-player-start-native.png")}
    report["changed_protected"] = session.result["changed_protected"]
    (OUT / "follow-single-start.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed")
    print(json.dumps(report, indent=2))


def follow_portmanteau() -> None:
    from PIL import ImageChops
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        session.click(1280, 1032)
        time.sleep(.55)
        session.click(1280, 900)
        time.sleep(.7)
        session.click(1970, 1218)
        time.sleep(5)
        session.capture("portmanteau-native")
        session.click(1370, 326)  # Second magic-item cell in the verified table.
        time.sleep(.4)
        session.capture("portmanteau-item-click")
        with Image.open(session.run / "portmanteau-native.png") as first, Image.open(session.run / "portmanteau-item-click.png") as second:
            difference = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
            # Ignore the clock at the upper left and measure inventory changes.
            region = difference.crop((1000, 200, 2240, 1440))
            changed = sum(max(pixel) > 8 for pixel in region.get_flattened_data())
        session.click(2130, 122)
        time.sleep(2)
        session.capture("portmanteau-after-ready")
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "fps": session.i(0x6DE6FD), "inventory_changed_pixels": changed,
                  "item_click": [1370, 326], "ready_click": [2130, 122],
                  "captures": dict(session.result["screenshots"]),
                  "controls_after": len(session.controls())}
    report["changed_protected"] = session.result["changed_protected"]
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed")
    (OUT / "follow-portmanteau.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def follow_menu() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        before = [row["rect"] for row in session.controls()]
        target = (1280, 912)
        if [680, 864, 1880, 960] not in before:
            raise RuntimeError("Load Game button not at scaled native coordinates")
        for event in (0x200, 0x201, 0x202):
            session.message(event, *target)
            time.sleep(0.08)
        time.sleep(1)
        session.capture("load-after-scaled-click")
        after = [row["rect"] for row in session.controls()]
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "load_menu_reached": [680, 864, 1880, 960] not in after,
                  "capture": str(session.run / "load-after-scaled-click.png"),
                  "control_count": len(after)}
        (OUT / "follow-menu.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


def follow_options() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    with DirectSession() as session:
        before = [row["rect"] for row in session.controls()]
        target = (1280, 1152)
        if [680, 1104, 1880, 1200] not in before:
            raise RuntimeError("Options button not at scaled native coordinates")
        for event in (0x200, 0x201, 0x202):
            session.message(event, *target)
            time.sleep(0.08)
        time.sleep(1)
        session.capture("options-after-scaled-click")
        after = [row["rect"] for row in session.controls()]
        report = {"surface": [session.i(0x6A49F0), session.i(0x6A49F4)],
                  "options_reached": [680, 1104, 1880, 1200] not in after,
                  "capture": str(session.run / "options-after-scaled-click.png"),
                  "control_count": len(after)}
        (OUT / "follow-options.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


def follow_test2() -> None:
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    report = {"stage": "started"}
    try:
        with DirectSession() as session:
            def click(x: int, y: int) -> None:
                for event in (0x200, 0x201, 0x202):
                    session.message(event, x, y)
                    time.sleep(0.08)
            click(1280, 912)
            time.sleep(0.7)
            rows = sorted((LAB / "Save").glob("*.sav"), key=lambda path: path.stat().st_mtime_ns, reverse=True)
            index = [path.stem.lower() for path in rows].index("test2")
            report["save_row"] = index
            click(1280, 584 + index * 48)
            time.sleep(0.25)
            click(656, 1332)
            time.sleep(5)
            if session.proc.poll() is not None:
                raise RuntimeError("Engine exited while loading test2")
            session.capture("test2-native-probe")
            report["stage"] = "captured"
            report["surface"] = [session.i(0x6A49F0), session.i(0x6A49F4)]
            scene = session.i(0x6C482C)
            if not 0x10000 < scene < 0x7FFFFFFF:
                raise RuntimeError("Invalid battle scene rectangle pointer")
            report["scene_rect"] = [session.i(scene + offset) for offset in (0, 4, 8, 12)]
            report["battle_surface"] = [session.i(0x6A49F0), session.i(0x6A49F4)]
            report["capture"] = str(session.run / "test2-native-probe.png")
    except Exception as error:
        report["stage"] = "failed"
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        (OUT / "follow-test2.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


def font_flow() -> None:
    """Exercise the adapted UI plus a read-only test2 load with enlarged fonts."""
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    report = {}
    with DirectSession() as session:
        report["font_metrics"] = session.font_metrics()
        session.click(1280, 1152)
        time.sleep(.6)
        session.capture("font-options")
        if [680, 1104, 1880, 1200] in [row["rect"] for row in session.controls()]:
            raise RuntimeError("Options screen not reached")
        session.click(1868, 1320)  # Cancel: preserve all preferences.
        time.sleep(.5)
        if [680, 864, 1880, 960] not in [row["rect"] for row in session.controls()]:
            raise RuntimeError("Options Cancel did not return to menu")
        session.click(1280, 912)
        time.sleep(.5)
        session.capture("font-load")
        rows = sorted((LAB / "Save").glob("*.sav"), key=lambda path: path.stat().st_mtime_ns, reverse=True)
        index = [path.stem.lower() for path in rows].index("test2")
        # Native list box rows use line height + the engine's two-pixel margin.
        row_height = report["font_metrics"]["small"]["line_height"] + 2
        session.click(1280, int(560 + (index + .5) * row_height))
        time.sleep(.3)
        session.capture("font-load-selected")
        session.click(656, 1332)
        time.sleep(5)
        if session.proc.poll() is not None:
            raise RuntimeError("Engine exited loading test2 with enlarged fonts")
        table = session.i(0x6DEF58)
        unit0 = [session.i(table + offset) for offset in (8, 12, 16)]
        if unit0 != [66, 48, 6] or session.i(0x6DEF5C) != 125:
            raise RuntimeError("Wrong test2 fixture after enlarged-font list selection")
        session.capture("font-test2")
        report.update(surface=session.result["checks"]["surface"], fps=session.i(0x6DE6FD),
                      selected_save="test2", save_row=index, list_row_height=row_height,
                      unit0=unit0, captures=dict(session.result["screenshots"]),
                      options_cancel=True, test2_load=True)
        for name in ("menu-native", "font-options", "font-load", "font-load-selected"):
            if session.result["images"][name]["bar_nonblack_fraction"] > .001:
                raise RuntimeError("Nonblack UI side bar: " + name)
    report["changed_protected"] = session.result["changed_protected"]
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed during font flow")
    (OUT / "font-flow.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    actions = {"prepare": prepare, "probe": probe, "advance-load": advance_load,
               "advance-options": advance_options, "advance-quick": advance_quick,
               "follow-menu": follow_menu, "follow-quick": follow_quick,
               "follow-single-setup": follow_single_setup,
               "follow-map-selection": follow_map_selection,
               "follow-single-start": follow_single_start,
               "follow-portmanteau": follow_portmanteau,
               "follow-options": follow_options, "follow-test2": follow_test2,
               "font-flow": font_flow}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit("usage: native_ui_2k_probe.py " + "|".join(actions))
    actions[sys.argv[1]]()
