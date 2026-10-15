"""Smoke-test the isolated, user-runnable mixed UI package and its v7 launcher."""
from __future__ import annotations

import ctypes
import csv
import io
import json
import os
import sys
from pathlib import Path
import shutil
import subprocess
import time

from PIL import Image, ImageChops

import wide169_trial
from native_ui_2k_probe import DirectSession
from native_ui_mixed_probe import load_test2
from verify_hd60_runtime import read
from wide169_build import ROOT, sha


ENGINE_SHA = "531ca844330ed03c4314e762a4f23f4b72db9ca30ec88608023103099ab80ac0"
WRAPPER_HASHES = {"mixed-ui-v1": "04a7dc723b26792deda0860fb48d91df79e5fd857f994c1de0d89b6dffccf17c",
                  "mixed-ui-v2": "bb9a1b662c9b16bc27fb4270d745b53852428f840a3caabd21f877e1bf03b68d"}


def main():
    version = "mixed-ui-v2" if "--v2" in sys.argv else "mixed-ui-v1"
    normal = "normal-startup" in sys.argv
    extended = "extended-flow" in sys.argv
    if extended and (version != "mixed-ui-v2" or normal):
        raise ValueError("extended-flow requires --v2 and background input")
    play = ROOT / "modernization/playtests" / version
    game, lab = play / "game", play / "game-wide169"
    ctypes.windll.user32.SetProcessDPIAware()
    wide169_trial.GAME, wide169_trial.LAB = game, lab
    import native_ui_mixed_probe
    native_ui_mixed_probe.LAB = lab
    session = DirectSession()
    if any(name.startswith("chaos") for _, _, name in wide169_trial.processes(session.k)):
        raise RuntimeError("A game is already running; refusing to interfere")
    engine = lab / "Chaos-Wide169-engine.exe"
    wrapper = lab / "ddraw.dll"
    if sha(engine.read_bytes()) != ENGINE_SHA or sha(wrapper.read_bytes()) != WRAPPER_HASHES[version]:
        raise RuntimeError("Unknown playtest engine or wrapper")
    mutable = {p: (p.read_bytes(), p.stat().st_atime_ns, p.stat().st_mtime_ns)
               for p in (*sorted((lab / "Save").glob("*")),
                         *sorted((lab / "CFG").glob("*.cfg")),
                         lab / "AI/EXPERIEN.DAT", lab / "AI/Brain.dat") if p.is_file()}
    before_saves = set((lab / "Save").glob("*"))
    launcher = None
    replay_log = lab / "modernization/logs/render-replay.csv"
    initial_log_bytes = replay_log.stat().st_size if replay_log.exists() else 0
    report = {"version": version, "engine_sha256": ENGINE_SHA,
              "wrapper_sha256": WRAPPER_HASHES[version],
              "mode": "normal-startup" if normal else "extended-flow" if extended else "background-flow"}
    def font_state():
        scene = session.i(0x6C482C)
        return {"mode": session.i(0x6E1F0C), "scene_pointer": scene,
                "scene_rect": [session.i(scene + offset) for offset in (0, 4, 8, 12)]
                              if 0x10000 < scene < 0x7FFFFFFF else None,
                "world_pointer": session.i(0x6A46BC),
                "controls": session.controls(),
                "text_entries": {hex(address): read(session.k, session.handle, address, 8).hex()
                                 for address in (0x4A5CE0, 0x4A6190, 0x4A6630, 0x4A58E0)},
                "font_heights": [session.i(session.i(address) + 16) for address in
                                 (0x6B0400, 0x656680, 0x6DF1C0)]}
    try:
        environment = dict(os.environ, MM_PROBE_MIXED_RENDER="1")
        if version == "mixed-ui-v2":
            environment["MM_PROBE_RENDER_LOG" if extended else "MM_PROBE_RENDER_LIGHT_LOG"] = "1"
        environment.pop("MM_PROBE_BACKGROUND_INPUT", None)
        if not normal:
            environment["MM_PROBE_BACKGROUND_INPUT"] = "1"
        launcher = subprocess.Popen([str(game / "Chaos-Mixed-UI-Preview.exe")], cwd=lab,
                                    env=environment)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            children = [pid for pid, parent, name in wide169_trial.processes(session.k)
                        if parent == launcher.pid and name == "chaos-wide169-engine.exe"]
            if children:
                break
            if launcher.poll() is not None:
                raise RuntimeError("Playtest launcher exited without an engine")
            time.sleep(.2)
        else:
            raise RuntimeError("Playtest engine did not start")
        session.pid = children[0]
        session.handle = session.k.OpenProcess(0x1011, False, session.pid)
        if not session.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        time.sleep(5)
        if launcher.poll() is not None:
            raise RuntimeError("Playtest engine or injection exited at startup")
        if not normal:
            session.channel = session.u.RegisterWindowMessageW("MagicMayhem.Probe.BackgroundMouse.v1")
            session.message(0)
        sites = {0x578610: 0xE9, 0x58BF40: 0xE9, 0x46C194: 0xE9,
                 0x509CA6: 0xE9, 0x4FDAD0: 0xE9, 0x4A54CF: 0xE8}
        report["qol_hooks"] = {hex(a): read(session.k, session.handle, a, 1) == bytes([op])
                               for a, op in sites.items()}
        if not all(report["qol_hooks"].values()):
            raise RuntimeError("v7 QoL hooks were not all injected")
        rect = ctypes.wintypes.RECT()
        session.u.GetClientRect(session.window(), ctypes.byref(rect))
        report["physical_client"] = [rect.right, rect.bottom]
        report["surface"] = [session.i(0x6A49F0), session.i(0x6A49F4)]
        report["fps_preference"] = session.i(0x6DE6FD)
        print("startup", report["physical_client"], report["surface"], report["fps_preference"], flush=True)
        if not normal:
            session.capture("playtest-menu")
            if extended:
                report["font_states"] = {"menu": font_state()}
            load_test2(session)
            if extended:
                report["font_states"]["battle"] = font_state()
            session.capture("playtest-battle")
            with Image.open(session.run / "playtest-battle.png") as image:
                rgb = image.convert("RGB")
                report["battle_exact_2x"] = rgb == rgb.resize((1280, 720), Image.Resampling.NEAREST).resize(
                    (2560, 1440), Image.Resampling.NEAREST)
            report["run"] = str(session.run)
            if version == "mixed-ui-v2":
                logfile = replay_log
                if logfile.exists():
                    with logfile.open("rb") as source:
                        source.seek(initial_log_bytes)
                        lines = source.read().decode("ascii", errors="replace").splitlines()
                else:
                    lines = []
                report["render_events"] = {name: sum("," + name + "," in line for line in lines)
                                           for name in ("viewport", "native", "replay", "ui_preserved")}
                if report["render_events"]["replay"] == 0:
                    raise RuntimeError("No distinct replay render in mixed mode")
            print("battle", report.get("battle_exact_2x"), report.get("render_events"), flush=True)
            if extended:
                session.key(0x1B)
                time.sleep(.5)
                session.capture("playtest-escape")
                escape_controls = [row["rect"] for row in session.controls()]
                if [460, 276, 820, 324] not in escape_controls:
                    raise RuntimeError("Esc Save Game control absent")
                session.click(1280, 600)
                time.sleep(.7)
                session.capture("playtest-save")
                report["font_states"]["save"] = font_state()
                report["save_control_native"] = [488, 1272, 848, 1392] in [
                    row["rect"] for row in session.controls()]
                with Image.open(session.run / "playtest-save.png") as got, Image.open(
                        lab / "Interface/SaveGame/800x600/Save Game 800-600.JPG") as expected:
                    diff = ImageChops.difference(got.convert("RGB").crop((320, 0, 2240, 1440)),
                                                 expected.convert("RGB").crop((320, 0, 2240, 1440)))
                    report["save_background_match_within_8"] = sum(
                        max(pixel) <= 8 for pixel in diff.get_flattened_data()) / (1920 * 1440)
                session.click(1876, 1332)
                time.sleep(.5)
                if [460, 276, 820, 324] in [row["rect"] for row in session.controls()]:
                    session.click(1280, 960)
                    time.sleep(.5)
                report["battle_menu_closed"] = [460, 276, 820, 324] not in [
                    row["rect"] for row in session.controls()]
                if not report["battle_menu_closed"]:
                    raise RuntimeError("Esc Cancel did not return to battle")
                session.capture("playtest-battle-return")
                report["font_states"]["battle_return"] = font_state()
                with Image.open(session.run / "playtest-battle-return.png") as opened:
                    image = opened.convert("RGB")
                    report["battle_return_exact_2x"] = image == image.resize(
                        (1280, 720), Image.Resampling.NEAREST).resize((2560, 1440), Image.Resampling.NEAREST)
                if not (report["battle_menu_closed"] and report["save_control_native"] and report["save_background_match_within_8"] > .9
                        and report["battle_return_exact_2x"]):
                    raise RuntimeError("Save Game round-trip rendering gate failed")
                # The native wizard portrait is a reliable selection target.
                session.click(2436, 1300)
                time.sleep(.3)
                report["wizard_selected"] = session.i(0x6E984C) == 1
                if not report["wizard_selected"]:
                    raise RuntimeError("Wizard selection was not confirmed")
                base = session.i(0x6DEF58)
                before = [session.i(base + offset) for offset in (8, 12, 16)]
                logfile = lab / "modernization/logs/render-replay.csv"
                log_start = logfile.stat().st_size if logfile.exists() else 0
                session.click(1400, 800, right=True)
                time.sleep(3)
                after = [session.i(base + offset) for offset in (8, 12, 16)]
                session.capture("playtest-moving")
                report["movement"] = {"before": before, "after": after, "world_changed": before != after}
                with logfile.open("rb") as source:
                    source.seek(log_start)
                    rows = list(csv.reader(io.TextIOWrapper(source, encoding="ascii", errors="replace")))
                frames = [row for row in rows if len(row) >= 12 and row[1] in ("native", "replay")]
                ui = [row for row in rows if len(row) >= 6 and row[1] == "ui_preserved"]
                moved = [row for row in frames if row[1] == "replay" and int(row[5]) > 0]
                changed = sum(left[4] != right[4] for left, right in zip(frames, frames[1:]))
                report["dynamic_render"] = {
                    "native": sum(row[1] == "native" for row in frames),
                    "replay": sum(row[1] == "replay" for row in frames),
                    "moved_replay": len(moved),
                    "adjacent_distinct_buffers": changed,
                    "ui_hash_preserved": sum(row[2] == row[3] and row[4] == "1" for row in ui),
                    "ui_hash_checks": len(ui),
                    "hashed_frames": sum(row[4] != "00000000" for row in frames),
                }
                print("extended", json.dumps({key: report[key] for key in (
                    "save_control_native", "save_background_match_within_8", "battle_return_exact_2x",
                    "wizard_selected", "movement", "dynamic_render")}), flush=True)
                if not report["movement"]["world_changed"] or not moved or not changed or not ui or any(
                        row[2] != row[3] or row[4] != "1" for row in ui):
                    raise RuntimeError("Movement or distinct-render gate failed")
        if (report["surface"] != [2560, 1440] or report["fps_preference"] != 30 or
                report["physical_client"] != [2560, 1440] or
                (not normal and not report["battle_exact_2x"])):
            raise RuntimeError("Playtest rendering gate failed")
    finally:
        if session.handle:
            session.k.TerminateProcess(session.handle, 0)
            session.k.CloseHandle(session.handle)
        if launcher:
            try:
                launcher.wait(timeout=5)
            except subprocess.TimeoutExpired:
                launcher.terminate()
                launcher.wait(timeout=5)
        for path, (data, atime, mtime) in mutable.items():
            path.write_bytes(data)
            os.utime(path, ns=(atime, mtime))
        for path in (lab / "Save").glob("*"):
            if path.is_file() and path not in before_saves:
                path.unlink()
    filename = "normal-startup-verification.json" if normal else "extended-verification.json" if extended else "verification.json"
    (play / filename).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
