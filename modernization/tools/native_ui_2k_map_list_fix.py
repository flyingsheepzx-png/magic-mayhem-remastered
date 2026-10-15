"""Keep enlarged map-list text inside its visible decorative frame."""
from __future__ import annotations

import json
from pathlib import Path

from native_ui_2k_probe import OUT, LAB, digest

CFG = Path("Interface/MapSelectionScreen/screen (Map Selection Screen).cfg")
OLD = b"Rect2=716,428,1844,1076"
NEW = b"Rect2=716,428,1844,1030"


def stage() -> None:
    build_path = OUT / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if "map_list_fix" in build:
        raise ValueError("Map list fix already staged")
    path = LAB / CFG
    before = path.read_bytes()
    if digest(before) != build["map_selection"]["cfg_sha256"] or before.count(OLD) != 1:
        raise ValueError("Unknown map selection CFG")
    after = before.replace(OLD, NEW)
    backup = OUT / "before-map-list-fix" / CFG
    if backup.exists():
        raise ValueError("Map list backup exists")
    backup.parent.mkdir(parents=True)
    backup.write_bytes(before)
    path.write_bytes(after)
    build["map_list_fix"] = {"before_sha256": digest(before), "after_sha256": digest(after),
                              "before_rect": OLD.decode(), "after_rect": NEW.decode()}
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["map_list_fix"], indent=2))


if __name__ == "__main__":
    stage()
