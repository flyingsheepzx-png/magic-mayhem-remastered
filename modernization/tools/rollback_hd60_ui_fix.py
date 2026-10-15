"""Rollback the 2026-09-27 HD UI follow-up in the playable lab copy.

This restores the preceding combined launcher/engine and the thirteen raster
assets added to the reversible UI-fit state by this follow-up.  Every current
and backup byte is hash-gated before anything is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


ROOT = (Path(__file__).resolve().parents[2] / "game")
BACKUP = ROOT / "modernization/backups/hd60-pre-ui-fix"
UI_STATE = ROOT / "modernization/assets/hd/ui-fit.json"
UI_BACKUP = ROOT / "modernization/assets/hd/backups/ui-fit"
PREVIOUS_UI_FILES = 270
CURRENT = {
    "Chaos-HD60-Trial.exe": "9ab567e1f720a440a6d1d52bdddbed85cfe5363917ff35ccf3a7791849c28a66",
    "Chaos-HD60-engine.exe": "b7414bb05f67bc80857f31cfce5ce07ccd755594f774f1878cfa93938c070744",
}
PREVIOUS = {
    "Chaos-HD60-Trial.exe": "8d350c61d8691c135028db334b7a1e6056341870706e48612c7e0eac2d49b0f0",
    "Chaos-HD60-engine.exe": "bd790add14ab1988471265e1e8d75f6d394e1166d83f009317127c63428636a4",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify rollback inputs without changing files")
    args = parser.parse_args()
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise RuntimeError("Refusing outside the marked playable HD lab")
    for name, expected in CURRENT.items():
        if sha(ROOT / name) != expected:
            raise RuntimeError(f"Current {name} hash is unknown; rollback refused")
    for name, expected in PREVIOUS.items():
        if sha(BACKUP / name) != expected:
            raise RuntimeError(f"Backup {name} hash is unknown; rollback refused")
    state = json.loads(UI_STATE.read_text(encoding="utf-8"))
    rows = state["files"]
    if len(rows) != 283:
        raise RuntimeError(f"Expected 283 fitted UI records, found {len(rows)}")
    restores = []
    for index, row in enumerate(rows[PREVIOUS_UI_FILES:], PREVIOUS_UI_FILES):
        live = ROOT / row["path"]
        original = UI_BACKUP / str(index)
        if sha(live) != row["applied_sha256"] or sha(original) != row["original_sha256"]:
            raise RuntimeError(f"UI hash mismatch at record {index}: {row['path']}")
        restores.append((live, original))
    if not args.check:
        for live, original in restores:
            shutil.copy2(original, live)
        state["files"] = rows[:PREVIOUS_UI_FILES]
        UI_STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        for name in CURRENT:
            shutil.copy2(BACKUP / name, ROOT / name)
    print(json.dumps({"mode": "check" if args.check else "rollback",
                      "rollback_ready": True,
                      "binaries": list(CURRENT),
                      "ui_files": len(restores),
                      "resulting_ui_state_files": PREVIOUS_UI_FILES}, indent=2))


if __name__ == "__main__":
    main()
