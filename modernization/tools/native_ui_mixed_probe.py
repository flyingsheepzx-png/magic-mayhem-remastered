"""Owned, hash-gated diagnostics for native UI / 1280x720 battle composition."""
from __future__ import annotations

import json
import sys
import time
from ctypes import wintypes as W
from PIL import Image, ImageChops

from native_ui_2k_probe import OUT, LAB, DirectSession, wide169_trial


def state(session):
    scene = session.i(0x6C482C)
    fields = {hex(a): session.i(a) for a in
              (0x6E1F68, 0x6A46BC, 0x6A49F0, 0x6A49F4,
               0x6A4FF0, 0x6A4FF4, 0x6F98C0, 0x642C68, 0x6DE6FD)}
    fields["scene_rect"] = [session.i(scene + o) for o in (0, 4, 8, 12)] if 0x10000 < scene < 0x7fffffff else None
    fields["scene_rect_pointer"] = scene
    fields["scene_owner_fields"] = {hex(o): session.i(scene - 0x11 + o) for o in
                                    (0x11, 0x15, 0x19, 0x1D, 0x21, 0x25, 0x31, 0x35)} if 0x10000 < scene < 0x7fffffff else None
    fields["font_objects"] = {hex(a): [session.i(a + o) for o in (0, 4, 8, 12, 16, 20, 0x220, 0x230)]
                              for a in (0x6B0400, 0x656680, 0x6DF1C0)}
    fields["battle_pointer"] = session.i(0x6A2DD0 + 0x18EC)
    obj = fields["0x6a46bc"]
    fields["scene_object"] = {hex(o): session.i(obj + o) for o in
                              (0x11, 0x15, 0x19, 0x1D, 0x21, 0x25, 0x2D, 0x31)} if 0x10000 < obj < 0x7fffffff else None
    return fields


def load_test2(session):
    session.click(1280, 912)
    time.sleep(.5)
    rows = sorted((LAB / "Save").glob("*.sav"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    index = [p.stem.lower() for p in rows].index("test2")
    session.click(1280, int(560 + (index + .5) * 46))
    time.sleep(.25)
    session.click(656, 1332)
    time.sleep(5)
    table = session.i(0x6DEF58)
    if [session.i(table + o) for o in (8, 12, 16)] != [66, 48, 6] or session.i(0x6DEF5C) != 125:
        raise RuntimeError("Not test2 fixture")


def inspect():
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    report = {}
    with DirectSession() as session:
        report["menu"] = state(session)
        load_test2(session)
        report["battle"] = state(session)
        session.capture("mixed-battle")
        session.key(0x1B)
        time.sleep(.5)
        report["escape"] = state(session)
        session.capture("mixed-inspect-escape")
        report["escape_controls"] = session.controls()
        session.key(0x1B)
        time.sleep(.4)
        session.key(ord("G"))
        time.sleep(.5)
        report["g_key"] = state(session)
        session.capture("mixed-inspect-g-key")
        report["run"] = str(session.run)
    report["changed_protected"] = session.result["changed_protected"]
    (OUT / "mixed-inspect.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def follow_save_game():
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    report = {}
    with DirectSession() as session:
        load_test2(session)
        session.key(0x1B)
        time.sleep(.5)
        menu = [row["rect"] for row in session.controls()]
        if [460, 276, 820, 324] not in menu:
            raise RuntimeError("Existing battle Esc Save Game control absent")
        session.click(640, 300)
        time.sleep(.7)
        session.capture("mixed-save-game")
        control_rects = [row["rect"] for row in session.controls()]
        with Image.open(session.run / "mixed-save-game.png") as got, Image.open(
                LAB / "Interface/SaveGame/800x600/Save Game 800-600.JPG") as expected:
            observed = got.convert("RGB").crop((320, 0, 2240, 1440))
            reference = expected.convert("RGB").crop((320, 0, 2240, 1440))
            difference = ImageChops.difference(observed, reference)
            matches = sum(max(pixel) <= 8 for pixel in difference.get_flattened_data())
            match_ratio = matches / (1920 * 1440)
        report.update(surface=state(session), controls=control_rects,
                      background_match_within_8=match_ratio,
                      capture=str(session.run / "mixed-save-game.png"))
        if match_ratio < .85:
            raise RuntimeError("Save Game background not full-size")
        session.key(0x1B)
        time.sleep(.4)
        report["cancel_control_count"] = len(session.controls())
    report["changed_protected"] = session.result["changed_protected"]
    if report["changed_protected"]:
        raise RuntimeError("Protected files changed")
    (OUT / "follow-save-game.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def write_save_game():
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    target = LAB / "Save/hdprobe.sav"
    if target.exists():
        raise RuntimeError("Diagnostic save name already exists")
    report = {}
    with DirectSession() as session:
        load_test2(session)
        session.key(0x1B)
        time.sleep(.4)
        session.click(640, 300)
        time.sleep(.6)
        controls = [row["rect"] for row in session.controls()]
        if [712, 360, 1848, 460] not in controls or [488, 1272, 848, 1392] not in controls:
            raise RuntimeError("Scaled save controls absent")
        session.click(1200, 410)
        time.sleep(.2)
        for _ in range(40):
            session.key(8)
        session.u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
        for ch in "hdprobe":
            session.u.PostMessageW(session.window(), 0x102, ord(ch), 0)
            time.sleep(.08)
        session.capture("mixed-save-name")
        session.click(668, 1332)
        time.sleep(1.5)
        report = {"created": target.exists(), "bytes": target.stat().st_size if target.exists() else 0,
                  "name_capture": str(session.run / "mixed-save-name.png"),
                  "after_controls": len(session.controls())}
        if not report["created"] or report["bytes"] < 1000:
            raise RuntimeError("Native-size Save Game action failed")
    report["changed_protected"] = session.result["changed_protected"]
    report["save_removed_in_cleanup"] = not target.exists()
    if report["changed_protected"] or not report["save_removed_in_cleanup"]:
        raise RuntimeError("Diagnostic cleanup incomplete")
    (OUT / "write-save-game.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    {"inspect": inspect, "follow-save-game": follow_save_game,
     "write-save-game": write_save_game}[sys.argv[1]]()
