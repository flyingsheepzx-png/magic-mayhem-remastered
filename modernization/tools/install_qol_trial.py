"""Hash-gated install, verify, status and rollback for the isolated QoL trial."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

import pefile

ROOT = (Path(__file__).resolve().parents[2] / "game")
SOURCE = ROOT / "modernization/build/Chaos-QoL-Trial.exe"
TARGET = ROOT / "Chaos-QoL-Trial.exe"
QOL = ROOT / "modernization/build/qol_bindings_trial.dll"
FULL = ROOT / "modernization/runtime/releases/full60_v1/full_trial.dll"
BASELINE = ROOT / "modernization/baseline/Chaos.exe"
CHILD = ROOT / "Chaos-singleplayer-600.exe"
CONFIG = ROOT / "modernization/config/qol-hotkeys.json"
MANIFEST = ROOT / "modernization/qol-trial-installed.json"
BACKUP_DIR = ROOT / "modernization/backups/qol_trial"
EXPECTED = {
    BASELINE: "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291",
    CHILD: "856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd",
    FULL: "3d0c7101d825fb14e885b9acf2f9e44383c2d9706c27c31a999187add066f59b",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def modules(launcher: Path) -> dict[int, str]:
    pe = pefile.PE(str(launcher))
    if pe.FILE_HEADER.Machine != 0x14C:
        raise RuntimeError("Launcher is not x86")
    result = {}
    for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if resource_type.id != 10:
            continue
        for resource in resource_type.directory.entries:
            for language in resource.directory.entries:
                data = pe.get_data(language.data.struct.OffsetToData,
                                   language.data.struct.Size)
                result[resource.id] = hashlib.sha256(data).hexdigest()
    return result


def verify_build() -> tuple[str, str]:
    for path, digest in EXPECTED.items():
        if not path.is_file() or sha(path) != digest:
            raise RuntimeError(f"Unknown or missing dependency: {path}")
    if not QOL.is_file() or not SOURCE.is_file():
        raise RuntimeError("Build the separate QoL DLL and trial launcher first")
    if pefile.PE(str(QOL)).FILE_HEADER.Machine != 0x14C:
        raise RuntimeError("QoL module is not x86")
    if modules(SOURCE) != {101: EXPECTED[FULL], 102: sha(QOL)}:
        raise RuntimeError("Trial launcher does not embed the verified modules")
    if (ROOT / "CFG/prefs.cfg").read_bytes().count(b"MaxFramesPerSec=30") != 1:
        raise RuntimeError("Installed 30-Hz preference changed")
    from sys import path as sys_path
    sys_path.insert(0, str(ROOT / "modernization"))
    from qol_bindings import Layout
    Layout.load(CONFIG)
    return sha(SOURCE), sha(QOL)


def no_game_running() -> None:
    from install_full60 import no_game_running as check
    check()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "verify", "status", "rollback"))
    args = parser.parse_args()
    source_sha, qol_sha = verify_build()
    current = sha(TARGET) if TARGET.is_file() else None
    if args.action == "status":
        print(json.dumps({"entry": str(TARGET), "installed": current == source_sha,
                          "entry_sha256": current, "build_sha256": source_sha}, indent=2))
        return
    previous_sha = None
    if MANIFEST.is_file():
        previous_sha = json.loads(MANIFEST.read_text(encoding="utf-8")).get("launcher_sha256")
    if current not in (None, source_sha, previous_sha):
        raise RuntimeError("Unknown trial entry; change refused")
    if args.action == "verify":
        if current != source_sha or modules(TARGET) != modules(SOURCE):
            raise RuntimeError("Trial entry missing or resource mismatch")
        print(json.dumps({"verified": str(TARGET), "launcher_sha256": current,
                          "qol_module_sha256": qol_sha}, indent=2))
        return
    no_game_running()
    if args.action == "rollback":
        if current is not None:
            TARGET.unlink()
        print(json.dumps({"removed": str(TARGET), "configuration_preserved": str(CONFIG)}, indent=2))
        return
    preserved = [ROOT / "Chaos.exe", CHILD, ROOT / "ddraw.dll", ROOT / "ddraw.ini",
                 ROOT / "CFG/prefs.cfg", *sorted((ROOT / "Save").glob("*.sav"))]
    before = {str(path): sha(path) for path in preserved}
    if current is not None and current != source_sha:
        previous = BACKUP_DIR / f"Chaos-QoL-Trial-{current}.exe"
        previous.parent.mkdir(parents=True, exist_ok=True)
        if previous.exists() and sha(previous) != current:
            raise RuntimeError("Previous trial backup differs; upgrade refused")
        if not previous.exists():
            shutil.copy2(TARGET, previous)
        if sha(previous) != current:
            raise RuntimeError("Previous trial backup failed verification")
    if current != source_sha:
        temporary = TARGET.with_name(TARGET.name + ".installing")
        try:
            shutil.copy2(SOURCE, temporary)
            if sha(temporary) != source_sha:
                raise RuntimeError("Staged launcher hash changed")
            os.replace(temporary, TARGET)
        finally:
            if temporary.exists():
                temporary.unlink()
    if any(sha(Path(path)) != digest for path, digest in before.items()):
        if sha(TARGET) == source_sha:
            TARGET.unlink()
        raise RuntimeError("An existing game or save file changed")
    MANIFEST.write_text(json.dumps({"entry": str(TARGET), "launcher_sha256": source_sha,
                                    "qol_module_sha256": qol_sha,
                                    "frozen_module_sha256": EXPECTED[FULL],
                                    "original_engine_sha256": EXPECTED[BASELINE],
                                    "child_engine_sha256": EXPECTED[CHILD],
                                    "preserved": before,
                                    "rollback": "python modernization/tools/install_qol_trial.py rollback",
                                    "status": "experimental binding trial; visual labels and runtime validation pending"},
                                   indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"installed": str(TARGET), "launcher_sha256": source_sha,
                      "rollback": "python modernization/tools/install_qol_trial.py rollback"}, indent=2))


if __name__ == "__main__":
    main()
