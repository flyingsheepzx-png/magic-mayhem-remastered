"""Launch the selected resolution tier in the isolated game copy.

The 2K tier is an opt-in 1120x840 battle viewport presented at 1920x1440.
The main menu fills the expanded surface. --dry-run verifies the setup
without starting a game process.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from hd_resolution import EXE_SHA, ROOT, STATE
from hd_hud_build import build as build_hud
from hd_ui_fit import SAMPLE_SELECTION, apply as fit_ui, keyed_bmps as fit_keyed_bmps, samples as fit_samples


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise SystemExit("Refusing outside marked isolated game copy")
    if sha(ROOT / "Chaos.exe") != EXE_SHA:
        raise SystemExit("Unknown community executable")
    if not STATE.exists():
        raise SystemExit("Select a resolution tier with hd_resolution.py first")
    state = json.loads(STATE.read_text(encoding="utf-8"))
    for name, path in (("prefs", ROOT / "CFG/prefs.cfg"), ("ddraw", ROOT / "ddraw.ini")):
        if sha(path) != state["applied_hashes"][name]:
            raise SystemExit("Resolution configuration changed outside selector: " + name)
    tier = state["tier"]
    if tier == "2k":
        hud = build_hud()
        executable = Path(hud["target"])
        battle_surface = [1120, 840]
    elif tier in ("640", "800"):
        executable = ROOT / "Chaos.exe"
        battle_surface = [640, 480] if tier == "640" else [800, 600]
    else:
        raise SystemExit("Unknown resolution tier")
    report = {"tier": tier, "executable": str(executable), "sha256": sha(executable),
              "battle_surface": battle_surface,
              "ui_status": "expanded main menu and bottom-right battle HUD" if tier == "2k" else "community layout",
              "dry_run": args.dry_run}
    print(json.dumps(report, indent=2))
    if not args.dry_run:
        fit_ui(tier == "2k")
        if tier == "2k" and SAMPLE_SELECTION.exists():
            fit_samples(True)
        if tier == "2k":
            fit_keyed_bmps()
        subprocess.Popen([str(executable)], cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
