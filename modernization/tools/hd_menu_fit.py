"""Fit the isolated main menu to 1120x840, with tier-specific verified rollback.

The engine still requests the 800 resource filename. Only the HD sibling has
an enlarged menu backing surface; the compatibility JPEG and Rect2 layout
follow that surface. Rect1 and the community executable remain unchanged.
"""
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image
from hd_menu_trial import ASSETS, SUPPORTED_EXE

ROOT = (Path(__file__).resolve().parents[2] / "game")
FILES = (ASSETS["menu"][0], Path("Interface/MainScreen/screen (MainMenu).cfg"))
STATE = ROOT / "modernization/assets/hd/menu-fit.json"
BACKUP = ROOT / "modernization/assets/hd/backups/menu-fit"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate():
    lab = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if lab.get("kind") != "isolated-hd-game-lab" or Path(lab["root"]).resolve() != ROOT:
        raise RuntimeError("Refusing outside isolated lab")
    if sha((ROOT / "Chaos.exe").read_bytes()) != SUPPORTED_EXE:
        raise RuntimeError("Unknown community executable")


def fitted_data():
    validate()
    if STATE.exists():
        state = json.loads(STATE.read_text())
        cfg = (BACKUP / "1").read_bytes()
        if sha(cfg) != state["original"][1]:
            raise RuntimeError("Menu configuration backup changed")
    else:
        cfg = (ROOT / FILES[1]).read_bytes()
    source = ROOT / ASSETS["menu"][1]
    manifest = json.loads(source.with_suffix(".png.json").read_text())
    if manifest["output_sha256"] != sha(source.read_bytes()) or manifest["source_sha256"] != ASSETS["menu"][2]:
        raise RuntimeError("Unverified generated menu")
    with Image.open(source) as image:
        if image.size != (1920, 1440) or image.format != "PNG":
            raise RuntimeError("Unexpected menu source dimensions")
        image = image.convert("RGB").resize((1120, 840), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=100, subsampling=0)
    pattern = rb"(?m)^(Rect2\s*=\s*)(\d+),(\d+),(\d+),(\d+)"
    def scale(match):
        return match[1] + b",".join(str((int(match[i]) * 7 + 2) // 5).encode() for i in range(2, 6))
    cfg, count = re.subn(pattern, scale, cfg)
    if count != 7:
        raise RuntimeError("Unexpected main menu Rect2 count")
    return (buffer.getvalue(), cfg)


def apply(enabled):
    validate()
    current = [(ROOT / p).read_bytes() for p in FILES]
    state = json.loads(STATE.read_text()) if STATE.exists() else None
    if state:
        if [sha(data) for data in current] != state["applied"]:
            raise RuntimeError("Main menu changed outside fit tool")
        originals = [(BACKUP / str(i)).read_bytes() for i in range(2)]
        if [sha(data) for data in originals] != state["original"]:
            raise RuntimeError("Menu backup hash mismatch")
    else:
        originals = current
    if not enabled:
        if state:
            for path, data in zip(FILES, originals):
                (ROOT / path).write_bytes(data)
            STATE.unlink()
        return
    desired = fitted_data()
    if not state:
        BACKUP.mkdir(parents=True, exist_ok=True)
        for i, data in enumerate(originals):
            (BACKUP / str(i)).write_bytes(data)
    for path, data in zip(FILES, desired):
        (ROOT / path).write_bytes(data)
    STATE.write_text(json.dumps({"original": [sha(d) for d in originals],
                                 "applied": [sha(d) for d in desired],
                                 "size": [1120, 840]}, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fit", "restore"))
    apply(parser.parse_args().mode == "fit")
