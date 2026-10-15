"""Select one of three isolated HD-lab display tiers, with verified rollback.

Use hd_launch.py to run the selected executable. In the 2K tier the 1120x840
battle viewport is presented at 1920x1440; the main menu fills that viewport.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import display
from hd_ui_fit import SAMPLE_SELECTION, apply as fit_ui, keyed_bmps as fit_keyed_bmps, samples as fit_samples

ROOT = (Path(__file__).resolve().parents[2] / "game")
STATE = ROOT / "modernization/assets/hd/resolution-state.json"
BACKUP = ROOT / "modernization/assets/hd/resolution-backup"
EXE_SHA = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
TIERS = {"640": ("FALSE", "0", "0"), "800": ("TRUE", "0", "0"),
         "2k": ("TRUE", "1920", "1440")}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prefs_with_high_res(data: bytes, setting: str) -> bytes:
    text = data.decode("cp1252")
    pattern = re.compile(r"(?m)^IsHighRes=(?:TRUE|FALSE)[ \t]*(\r?)$")
    if len(pattern.findall(text)) != 1:
        raise RuntimeError("Expected exactly one active IsHighRes entry")
    text = pattern.sub(lambda match: "IsHighRes=" + setting + match.group(1), text)
    return prefs_with_default_rate(text.encode("cp1252"))


def prefs_with_default_rate(data: bytes) -> bytes:
    text = data.decode("cp1252")
    pattern = re.compile(r"(?m)^MaxFramesPerSec=\d+[ \t]*(\r?)$")
    if len(pattern.findall(text)) != 1:
        raise RuntimeError("Expected exactly one active MaxFramesPerSec entry")
    return pattern.sub(lambda match: "MaxFramesPerSec=30" + match.group(1), text).encode("cp1252")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tier", choices=[*TIERS, "status", "restore"])
    args = parser.parse_args()
    marker = ROOT / "modernization/assets/hd/HD_LAB.json"
    lab = json.loads(marker.read_text(encoding="utf-8-sig"))
    if lab.get("kind") != "isolated-hd-game-lab" or Path(lab["root"]).resolve() != ROOT:
        raise SystemExit("Refusing to modify an unmarked game directory")
    if digest((ROOT / "Chaos.exe").read_bytes()) != EXE_SHA:
        raise SystemExit("Unknown executable hash")
    paths = {"prefs": ROOT / "CFG/prefs.cfg", "ddraw": ROOT / "ddraw.ini"}
    current = {name: path.read_bytes() for name, path in paths.items()}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None
    if args.tier == "status":
        print(json.dumps({"saved_tier": state.get("tier") if state else None,
                          "current_hashes": {name: digest(data) for name, data in current.items()}}, indent=2))
        return 0
    if state:
        for name, data in current.items():
            if digest(data) != state["applied_hashes"][name]:
                raise SystemExit("Configuration changed outside this tool: " + name)
        originals = {name: (BACKUP / name).read_bytes() for name in paths}
        if any(digest(originals[name]) != state["original_hashes"][name] for name in paths):
            raise SystemExit("Configuration backup hash mismatch")
    else:
        originals = current
        BACKUP.mkdir(parents=True, exist_ok=True)
        for name, data in originals.items():
            (BACKUP / name).write_bytes(data)
    if args.tier == "restore":
        fit_ui(False)
        if state:
            for name, path in paths.items():
                path.write_bytes(prefs_with_default_rate(originals[name])
                                 if name == "prefs" else originals[name])
            STATE.unlink()
        print("Restored original isolated-lab display configuration")
        return 0
    high_res, width, height = TIERS[args.tier]
    next_data = {
        "prefs": prefs_with_high_res(originals["prefs"], high_res),
        "ddraw": display.update_ddraw(originals["ddraw"].decode("cp1252"),
                                       {"width": width, "height": height,
                                        "windowed": "true", "fullscreen": "false"}).encode("cp1252"),
    }
    fit_ui(args.tier == "2k")
    if args.tier == "2k" and SAMPLE_SELECTION.exists():
        fit_samples(True)
    if args.tier == "2k":
        fit_keyed_bmps()
    for name, path in paths.items():
        path.write_bytes(next_data[name])
    report = {"tier": args.tier, "game_surface": [640, 480] if args.tier == "640" else
              [1120, 840] if args.tier == "2k" else [800, 600],
              "wrapper_output": [1920, 1440] if args.tier == "2k" else None,
              "native_2k_ui": False,
              "battle_viewport_expanded": args.tier == "2k",
              "launcher": "python modernization/tools/hd_launch.py",
              "original_hashes": {name: digest(data) for name, data in originals.items()},
              "applied_hashes": {name: digest(data) for name, data in next_data.items()}}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
