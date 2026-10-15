"""Apply reversible cnc-ddraw output profiles; does not change native game resolution."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = (Path(__file__).resolve().parents[2] / "game")
BASELINE = ROOT / "modernization" / "baseline"
PRESETS = {"1080p": (1920, 1080), "1440p": (2560, 1440), "4k": (3840, 2160)}
SETTINGS = ("width", "height", "fullscreen", "windowed", "maintas", "border")

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_baseline() -> None:
    manifest = json.loads((BASELINE / "manifest.json").read_text(encoding="utf-8"))
    for name in ("Chaos.exe", "ddraw.dll", "ddraw.ini"):
        expected = manifest["files"][name]["sha256"]
        if _sha256(BASELINE / name) != expected:
            raise RuntimeError(f"Baseline corrupt: {name}")
    if _sha256(ROOT / "Chaos.exe") != manifest["files"]["Chaos.exe"]["sha256"]:
        raise RuntimeError("Unsupported Chaos.exe version; no profile applied")
    if _sha256(ROOT / "ddraw.dll") != manifest["files"]["ddraw.dll"]["sha256"]:
        raise RuntimeError("Unsupported ddraw.dll version; no profile applied")

def update_ddraw(text: str, values: dict[str, str]) -> str:
    sections = list(re.finditer(r"(?m)^\[([^\]]+)\]\s*$", text))
    if not sections or sections[0].group(1).lower() != "ddraw":
        raise ValueError("Expected the cnc-ddraw [ddraw] section first")
    end = sections[1].start() if len(sections) > 1 else len(text)
    head, tail = text[:end], text[end:]
    for key, value in values.items():
        pattern = re.compile(rf"(?m)^({re.escape(key)}\s*=).*$")
        if len(pattern.findall(head)) != 1:
            raise ValueError(f"Expected exactly one [ddraw] setting: {key}")
        head = pattern.sub(lambda match: match.group(1) + value, head)
    return head + tail

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preset", choices=[*PRESETS, "restore"])
    parser.add_argument("--mode", choices=["window", "borderless"], default="window")
    args = parser.parse_args()
    verify_baseline()
    target = ROOT / "ddraw.ini"
    if args.preset == "restore":
        new_data = (BASELINE / "ddraw.ini").read_bytes()
    else:
        width, height = PRESETS[args.preset]
        values = dict(zip(SETTINGS, (
            str(width), str(height),
            "true" if args.mode == "borderless" else "false",
            "true", "true", "false" if args.mode == "borderless" else "true")))
        # Start from the backed-up community configuration to avoid cumulative edits.
        original = (BASELINE / "ddraw.ini").read_text(encoding="cp1252")
        new_data = update_ddraw(original, values).encode("cp1252")
    current = target.read_bytes()
    if current != new_data:
        temp = target.with_suffix(".ini.tmp")
        temp.write_bytes(new_data)
        temp.replace(target)
    print(f"Applied {args.preset} {args.mode if args.preset != 'restore' else ''}; game remains native 800x600")

if __name__ == "__main__":
    main()
