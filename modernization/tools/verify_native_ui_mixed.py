"""Owned mixed-render probe: rendered upload, 2x pixels and display input."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import json
import shutil
import time

from PIL import Image, ImageChops

from native_ui_2k_probe import OUT, LAB, DirectSession, wide169_trial
from native_ui_mixed_probe import load_test2, state


def query(session, event):
    value = W.DWORD_PTR() if hasattr(W, "DWORD_PTR") else ctypes.c_size_t()
    if not session.u.SendMessageTimeoutW(session.window(), session.channel, event, 0, 2, 2000, ctypes.byref(value)):
        raise RuntimeError("Mixed telemetry query timed out")
    return value.value


def pairs(path):
    with Image.open(path) as opened:
        image = opened.convert("RGB")
        reduced = image.resize((1280, 720), Image.Resampling.NEAREST)
        rebuilt = reduced.resize((2560, 1440), Image.Resampling.NEAREST)
        return ImageChops.difference(image, rebuilt).getbbox() is None


def main():
    wide169_trial.GAME = OUT / "game"
    wide169_trial.LAB = LAB
    report = {}
    with DirectSession() as session:
        report["menu"] = state(session)
        load_test2(session)
        session.capture("battle-2x")
        report["battle"] = state(session)
        report["battle_exact_2x_pixels"] = pairs(session.run / "battle-2x.png")
        report["d3d9_uploads_before"] = query(session, 0x8000 + 78)
        # Display-space move maps through the diagnostic wrapper. The private
        # native protocol of the original diagnostic DLL is unchanged.
        session.message(0x200, 1600, 800)
        time.sleep(.2)
        report["display_move_cursor"] = [session.i(0x6A4FF0), session.i(0x6A4FF4)]
        session.key(0x1B)
        time.sleep(.5)
        session.capture("escape-2x")
        report["escape_exact_2x_pixels"] = pairs(session.run / "escape-2x.png")
        if [460, 276, 820, 324] not in [c["rect"] for c in session.controls()]:
            raise RuntimeError("Esc Save Game control absent")
        session.click(1280, 600)
        time.sleep(.7)
        session.capture("save-ui-native")
        rects = [c["rect"] for c in session.controls()]
        report["save_controls_native"] = [488, 1272, 848, 1392] in rects
        with Image.open(session.run / "save-ui-native.png") as got, Image.open(
                LAB / "Interface/SaveGame/800x600/Save Game 800-600.JPG") as expected:
            diff = ImageChops.difference(got.convert("RGB").crop((320, 0, 2240, 1440)),
                                       expected.convert("RGB").crop((320, 0, 2240, 1440)))
            report["save_background_match_within_8"] = sum(max(p) <= 8 for p in diff.get_flattened_data()) / (1920 * 1440)
        session.click(1876, 1332)
        time.sleep(.5)
        session.key(0x1B)
        time.sleep(.5)
        session.capture("battle-after-save")
        report["battle_return_exact_2x_pixels"] = pairs(session.run / "battle-after-save.png")
        report["d3d9_uploads_after"] = query(session, 0x8000 + 78)
        report["fps_preference"] = session.i(0x6DE6FD)
        report["output_client"] = session.result["checks"]["output_client"]
        report["run"] = str(session.run)
        for source, name in (("battle-2x", "battle-mixed-live-2560x1440"),
                             ("save-ui-native", "save-mixed-live-2560x1440"),
                             ("menu-native", "menu-mixed-live-2560x1440")):
            shutil.copy2(session.run / (source + ".png"), OUT / (name + ".png"))
    report["changed_protected"] = session.result["changed_protected"]
    (OUT / "mixed-live-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if (not all(report[k] for k in ("battle_exact_2x_pixels", "escape_exact_2x_pixels", "save_controls_native", "battle_return_exact_2x_pixels"))
            or report["save_background_match_within_8"] < .9 or report["changed_protected"]
            or report["d3d9_uploads_after"] <= report["d3d9_uploads_before"]
            or report["fps_preference"] != 30):
        raise RuntimeError("Mixed rendering gate failed")


if __name__ == "__main__":
    main()
