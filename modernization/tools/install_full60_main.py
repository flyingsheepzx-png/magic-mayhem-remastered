"""Install the accepted single-player 30/60 candidate as the main Chaos.exe entry."""
import argparse
import json
import os
from pathlib import Path
import shutil

from install_full60 import embedded_module, no_game_running, sha


ROOT = (Path(__file__).resolve().parents[2] / "game")
TARGET = ROOT / "Chaos.exe"
SOURCE = ROOT / "modernization/build/Chaos-Main-Full60.exe"
BACKUP = ROOT / "modernization/backups/full60_main/Chaos.exe"
MANIFEST = ROOT / "modernization/full60-main-installed.json"
BASELINE = ROOT / "modernization/baseline/Chaos.exe"
ORIGINAL_SHA = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
MAIN_SHA = "ca93f3bd89c5770668021ebb04cd60e5684a9074512bceee86374ec54e22de84"
SIBLING_SHA = "856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd"
MODULE_SHA = "3d0c7101d825fb14e885b9acf2f9e44383c2d9706c27c31a999187add066f59b"
SEPARATE_SHA = "3b43276d2fae6851f37f21cbca37f564dc633ea100025ddec39a6a16b06030ad"


def verify_inputs():
    expected = {
        SOURCE: MAIN_SHA,
        BASELINE: ORIGINAL_SHA,
        ROOT / "Chaos-singleplayer-600.exe": SIBLING_SHA,
        ROOT / "Chaos-Optimized-60.exe": SEPARATE_SHA,
        ROOT / "modernization/runtime/releases/full60_v1/full_trial.dll": MODULE_SHA,
    }
    for path, digest in expected.items():
        if not path.is_file() or sha(path) != digest:
            raise RuntimeError(f"Unknown or missing build: {path}")
    if embedded_module(SOURCE) != MODULE_SHA:
        raise RuntimeError("Main launcher contains an unknown module")
    if (ROOT / "CFG/prefs.cfg").read_bytes().count(b"MaxFramesPerSec=30") != 1:
        raise RuntimeError("Expected 30-Hz preference exactly once")


def replace_verified(source, expected):
    temporary = TARGET.with_name(TARGET.name + ".full60-installing")
    try:
        shutil.copy2(source, temporary)
        if sha(temporary) != expected:
            raise RuntimeError("Staged executable hash mismatch")
        os.replace(temporary, TARGET)
        if sha(TARGET) != expected:
            raise RuntimeError("Installed executable hash mismatch")
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "rollback", "status"))
    args = parser.parse_args()
    current = sha(TARGET) if TARGET.is_file() else None
    if args.action == "status":
        print(json.dumps({"entry": str(TARGET), "sha256": current,
                          "installed": current == MAIN_SHA,
                          "original_backup_verified": BACKUP.is_file() and sha(BACKUP) == ORIGINAL_SHA,
                          "manifest": str(MANIFEST)}, indent=2))
        return
    no_game_running()
    if current not in (ORIGINAL_SHA, MAIN_SHA):
        raise RuntimeError("Unknown main executable; change refused")
    if args.action == "rollback":
        if current == ORIGINAL_SHA:
            print("Main executable is already original.")
            return
        if not BACKUP.is_file() or sha(BACKUP) != ORIGINAL_SHA:
            raise RuntimeError("Verified original backup missing; rollback refused")
        replace_verified(BACKUP, ORIGINAL_SHA)
        print(json.dumps({"restored": str(TARGET), "sha256": ORIGINAL_SHA,
                          "backup": str(BACKUP)}, indent=2))
        return
    verify_inputs()
    if BACKUP.exists() and sha(BACKUP) != ORIGINAL_SHA:
        raise RuntimeError("Unknown original backup; install refused")
    if not BACKUP.exists():
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET if current == ORIGINAL_SHA else BASELINE, BACKUP)
        if sha(BACKUP) != ORIGINAL_SHA:
            raise RuntimeError("Original backup verification failed")
    preserved = [ROOT / "Chaos-singleplayer-600.exe", ROOT / "Chaos-Optimized-60.exe",
                 ROOT / "ddraw.dll", ROOT / "ddraw.ini", ROOT / "CFG/prefs.cfg"]
    preserved += sorted((ROOT / "Save").glob("*.sav"))
    before = {str(path): sha(path) for path in preserved}
    if current == ORIGINAL_SHA:
        replace_verified(SOURCE, MAIN_SHA)
    if any(sha(Path(path)) != digest for path, digest in before.items()):
        replace_verified(BACKUP, ORIGINAL_SHA)
        raise RuntimeError("A preserved game file changed during installation")
    data = {"entry": str(TARGET), "launcher_sha256": MAIN_SHA,
            "original_sha256": ORIGINAL_SHA, "original_backup": str(BACKUP),
            "game_child": str(ROOT / "Chaos-singleplayer-600.exe"),
            "game_child_sha256": SIBLING_SHA, "embedded_module_sha256": MODULE_SHA,
            "frozen_module": str(ROOT / "modernization/runtime/releases/full60_v1/full_trial.dll"),
            "preserved_hashes": before,
            "scope": "single player, 800x600 native renderer, 30 logic preference",
            "2k_merge": "Keep the original backup for address-based 2K patches; compose with the frozen module only after 2K validation.",
            "rollback": "python modernization/tools/install_full60_main.py rollback"}
    MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"installed": str(TARGET), "sha256": MAIN_SHA,
                      "embedded_module_verified": True, "preserved_files_unchanged": True,
                      "rollback": data["rollback"]}, indent=2))


if __name__ == "__main__":
    main()
