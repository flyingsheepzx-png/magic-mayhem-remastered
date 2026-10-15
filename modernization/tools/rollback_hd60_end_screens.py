"""Restore the playable HD60 launcher and engine from before the end-screen fix."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


ROOT = (Path(__file__).resolve().parents[2] / "game")
BACKUP = ROOT / "modernization/backups/hd60-pre-end-screens"
PREVIOUS = {
    "Chaos-HD60-Trial.exe": "9ab567e1f720a440a6d1d52bdddbed85cfe5363917ff35ccf3a7791849c28a66",
    "Chaos-HD60-engine.exe": "b7414bb05f67bc80857f31cfce5ce07ccd755594f774f1878cfa93938c070744",
}
CURRENT = {
    "Chaos-HD60-Trial.exe": "4ed7bb070dad1c135cdf26b53f5f179fdddd87b11115d0a5150a7b94b939d2a7",
    "Chaos-HD60-engine.exe": "b05d382387ef1727c8df33c77b03fbd6b934c9d09e5c889cff99b5d4afd6545e",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise RuntimeError("Unexpected playable checkout")
    for name in CURRENT:
        if sha(ROOT / name) != CURRENT[name] or sha(BACKUP / name) != PREVIOUS[name]:
            raise RuntimeError(f"Unknown current or backup bytes: {name}")
    if not args.check:
        for name in CURRENT:
            shutil.copy2(BACKUP / name, ROOT / name)
    print(json.dumps({"mode": "check" if args.check else "rollback", "ready": True,
                      "files": list(CURRENT)}, indent=2))


if __name__ == "__main__":
    main()
