"""Install or remove the user-accepted single-player slope rerouting entry."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = (Path(__file__).resolve().parents[2] / "game")
LAUNCHER_SHA = "9f3586a1b47fb3bcde847bdc6734abbe0c232d60e2286c13b70f8085d34d25ba"
MODULE_SHA = "a1afc242539db725e28fe506ec321098416d9b0b2ff3d4e301f5b79c1e8d871e"
SUPPORTED = {
    "Chaos.exe": "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291",
    "Chaos-singleplayer-600.exe": "856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "rollback", "status"))
    args = parser.parse_args()
    target = ROOT / "Chaos-Optimized.exe"
    manifest = ROOT / "modernization/repath-installed.json"
    if args.action == "status":
        print(json.dumps({"installed": target.exists(),
                          "verified": target.exists() and digest(target) == LAUNCHER_SHA,
                          "manifest": str(manifest)}, indent=2))
        return
    active = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True)
    import csv
    names = {row[0].lower() for row in csv.reader(active.splitlines()) if row}
    if names & {"chaos-optimized.exe", "chaos-singleplayer-600.exe", "chaos.exe",
                "chaos-repath-slope-trial.exe", "chaos-repath-animation-trial.exe"}:
        raise RuntimeError("Close this game's running processes before changing the installed entry")
    if args.action == "rollback":
        if target.exists():
            if target.resolve().parent != ROOT or digest(target) != LAUNCHER_SHA:
                raise RuntimeError("Unknown installed entry; removal refused")
            target.unlink()
        # Keep the installation/backup manifest as a durable rollback record.
        print("Accepted rerouting entry removed. Game files and saves unchanged.")
        return
    for name, expected in SUPPORTED.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"Unsupported executable: {name}")
    source = ROOT / "modernization/build/Chaos-Optimized.exe"
    if digest(source) != LAUNCHER_SHA:
        raise RuntimeError("Unknown launcher build; installation refused")
    if target.exists() and digest(target) != LAUNCHER_SHA:
        raise RuntimeError("Existing unknown launcher; overwrite refused")
    preserved = [ROOT / name for name in SUPPORTED] + [ROOT / "ddraw.dll", ROOT / "ddraw.ini", ROOT / "CFG/prefs.cfg"]
    preserved += list((ROOT / "Save").glob("*.sav"))
    before = {p: digest(p) for p in preserved}
    backup = ROOT / "modernization/logs" / f"repath-install-{time.time_ns()}"
    backup.mkdir(parents=True)
    backups = []
    for p in preserved[:5]:
        dest = backup / p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        if digest(dest) != before[p]:
            raise RuntimeError("Installation backup verification failed")
        backups.append({"path": str(p), "backup": str(dest), "sha256": before[p]})
    shutil.copy2(source, target)
    if digest(target) != LAUNCHER_SHA or any(digest(p) != expected for p,expected in before.items()):
        raise RuntimeError("Installation verification failed")
    data = {"entry": str(target), "launcher_sha256": LAUNCHER_SHA,
            "embedded_module_sha256": MODULE_SHA,
            "accepted_trial_sha256": "c92332c88fd766897b0aea2e15ddc4233fc96dec6f4954e81f315af1d3be7bf3",
            "features": ["native search allowance 600", "protagonist mid-segment reroute", "native slope validation", "animation root-motion handoff"],
            "known_limitations": ["Rare drift on complex terrain reported by user", "Only protagonist mid-segment rerouting validated", "30-tick time compensation and real 60 FPS incomplete"],
            "backups": backups, "preserved_hashes": {str(p):h for p,h in before.items()},
            "rollback": "python modernization/tools/install_repath_slope.py rollback"}
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    (backup / "installation.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"installed": str(target), "verified": True,
                      "manifest": str(manifest), "game_files_and_saves_preserved": True}, indent=2))


if __name__ == "__main__":
    main()
