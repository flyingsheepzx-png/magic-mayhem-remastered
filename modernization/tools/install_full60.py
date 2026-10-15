"""Install or roll back the frozen, user-accepted single-player 30/60 entry."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import time

ROOT = (Path(__file__).resolve().parents[2] / "game")
SOURCE = ROOT / "modernization/build/Chaos-Optimized-60.exe"
TARGET = ROOT / "Chaos-Optimized-60.exe"
FROZEN = ROOT / "modernization/runtime/releases/full60_v1"
MANIFEST = ROOT / "modernization/full60-installed.json"
LAUNCHER_SHA = "3b43276d2fae6851f37f21cbca37f564dc633ea100025ddec39a6a16b06030ad"
MODULE_SHA = "3d0c7101d825fb14e885b9acf2f9e44383c2d9706c27c31a999187add066f59b"
TRIAL_SHA = "e7841ad3087061a7b87bea51050272a6550a4eb284ffaddf3ec91f4de29354a0"
KNOWN_EXES = {
    "Chaos.exe": ("b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291",
                  "ca93f3bd89c5770668021ebb04cd60e5684a9074512bceee86374ec54e22de84"),
    "Chaos-singleplayer-600.exe": "856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd",
    "Chaos-Optimized.exe": "9f3586a1b47fb3bcde847bdc6734abbe0c232d60e2286c13b70f8085d34d25ba",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embedded_module(path):
    import pefile

    pe = pefile.PE(str(path))
    try:
        entries = [entry for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries
                   if kind.id == 10 for name in kind.directory.entries
                   if name.id == 101 for entry in name.directory.entries]
        if len(entries) != 1:
            raise RuntimeError(f"Unexpected embedded module in {path}")
        data = entries[0].data.struct
        return hashlib.sha256(pe.get_data(data.OffsetToData, data.Size)).hexdigest()
    finally:
        pe.close()


def no_game_running():
    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                    ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                    ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    kernel.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    names = set()
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        if not kernel.Process32FirstW(handle, ctypes.byref(entry)):
            raise ctypes.WinError(ctypes.get_last_error())
        while True:
            names.add(entry.szExeFile.lower())
            if not kernel.Process32NextW(handle, ctypes.byref(entry)):
                break
    finally:
        kernel.CloseHandle(handle)
    active = names & {"chaos.exe", "chaos-singleplayer-600.exe", "chaos-optimized.exe",
                      "chaos-optimized-60.exe", "chaos-full-60-trial.exe"}
    if active:
        raise RuntimeError(f"Close active game processes before install/rollback: {sorted(active)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "rollback", "status"))
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps({"installed": TARGET.exists(),
                          "verified": TARGET.is_file() and sha(TARGET) == LAUNCHER_SHA,
                          "manifest": str(MANIFEST)}, indent=2))
        return
    no_game_running()
    if args.action == "rollback":
        if TARGET.exists():
            if TARGET.resolve().parent != ROOT or sha(TARGET) != LAUNCHER_SHA:
                raise RuntimeError("Unknown installed entry; removal refused")
            TARGET.unlink()
        print("Full-60 entry removed; existing game files, saves and reroute entry retained.")
        return
    for name, expected in KNOWN_EXES.items():
        if sha(ROOT / name) not in (expected if isinstance(expected, tuple) else (expected,)):
            raise RuntimeError(f"Unknown executable {name}; install refused")
    prefs = ROOT / "CFG/prefs.cfg"
    if prefs.read_bytes().count(b"MaxFramesPerSec=30") != 1:
        raise RuntimeError("Expected installed 30-Hz preference exactly once")
    frozen_dll = FROZEN / "full_trial.dll"
    frozen_trial = FROZEN / "Chaos-Full-60-Trial.exe"
    if (sha(SOURCE) != LAUNCHER_SHA or sha(frozen_dll) != MODULE_SHA or
            sha(frozen_trial) != TRIAL_SHA or
            embedded_module(SOURCE) != MODULE_SHA or
            embedded_module(frozen_trial) != MODULE_SHA):
        raise RuntimeError("Frozen launcher or embedded module hash mismatch")
    source_hashes = json.loads((FROZEN / "source-hashes.json").read_text(encoding="utf-8"))
    if any(sha(FROZEN / name) != expected for name, expected in source_hashes.items()):
        raise RuntimeError("Frozen source hash mismatch")
    if TARGET.exists() and sha(TARGET) != LAUNCHER_SHA:
        raise RuntimeError("Unknown installed entry; overwrite refused")
    preserved = [ROOT / name for name in KNOWN_EXES]
    preserved += [ROOT / "ddraw.dll", ROOT / "ddraw.ini", prefs]
    preserved += sorted((ROOT / "Save").glob("*.sav"))
    before = {str(path): sha(path) for path in preserved}
    backup = ROOT / "modernization/logs" / f"full60-install-{time.time_ns()}"
    backup.mkdir(parents=True)
    backed_up = []
    for path in preserved[:6]:
        dest = backup / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        if sha(dest) != before[str(path)]:
            raise RuntimeError("Backup verification failed")
        backed_up.append({"path": str(path), "backup": str(dest),
                           "sha256": before[str(path)]})
    temporary = TARGET.with_name(TARGET.name + ".installing")
    try:
        shutil.copy2(SOURCE, temporary)
        if sha(temporary) != LAUNCHER_SHA:
            raise RuntimeError("Launcher copy verification failed")
        temporary.replace(TARGET)
        if sha(TARGET) != LAUNCHER_SHA or any(sha(Path(path)) != digest
                                             for path, digest in before.items()):
            raise RuntimeError("Installation changed a preserved file")
    finally:
        if temporary.exists():
            temporary.unlink()
    data = {
        "entry": str(TARGET), "launcher_sha256": LAUNCHER_SHA,
        "embedded_module_sha256": MODULE_SHA, "accepted_trial_sha256": TRIAL_SHA,
        "source": str(FROZEN), "source_sha256": source_hashes,
        "backups": backed_up, "preserved_hashes": before,
        "scope": "single-player, 800x600 battle renderer and 30-Hz preference",
        "features": ["search allowance 600", "mid-segment protagonist rerouting",
                     "30-Hz timing trial", "intermediate rendered frame replay"],
        "limitations": ["60 distinct frames per second not established",
                        "rare drift on complex terrain", "full combat, save/load, FMV and alt-tab gates incomplete",
                        "multiplayer remains on the original entry"],
        "rollback": "python modernization/tools/install_full60.py rollback",
    }
    MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")
    (backup / "installation.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"installed": str(TARGET), "verified": True,
                      "manifest": str(MANIFEST), "preserved_files_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
