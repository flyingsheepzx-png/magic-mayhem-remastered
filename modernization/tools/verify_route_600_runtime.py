"""Start the opt-in game briefly and read its route limit without UI clicks."""
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import time

from route_600_build import ROOT, SOURCE, TARGET, BASE_SHA256, expected_image, sha256


def main():
    expected, _ = expected_image()
    if sha256(TARGET.read_bytes()) != sha256(expected):
        raise RuntimeError("Opt-in executable hash mismatch")
    if '"chaos.exe"' in subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Chaos.exe", "/FO", "CSV"], text=True).lower():
        raise RuntimeError("Close the ordinary game before this short test")
    saves = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (ROOT / "Save").glob("*.sav")}
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                         ctypes.c_void_p, ctypes.c_size_t,
                                         ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    proc = subprocess.Popen([str(TARGET)], cwd=ROOT)
    value = None
    try:
        for _ in range(20):
            if proc.poll() is not None:
                raise RuntimeError(f"Opt-in game exited early: {proc.returncode}")
            handle = kernel.OpenProcess(0x1000 | 0x10, False, proc.pid)
            if handle:
                try:
                    word = wintypes.DWORD()
                    read = ctypes.c_size_t()
                    if kernel.ReadProcessMemory(handle, 0x5E174C, ctypes.byref(word), 4,
                                                ctypes.byref(read)) and read.value == 4:
                        value = word.value
                        if value == 600:
                            break
                finally:
                    kernel.CloseHandle(handle)
            time.sleep(0.25)
        if value != 600:
            raise RuntimeError(f"Route limit did not load as 600: {value}")
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
    changed = [path for path, digest in saves.items()
               if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest]
    if changed:
        raise RuntimeError(f"Saves changed during startup: {changed}")
    if sha256(SOURCE.read_bytes()) != BASE_SHA256:
        raise RuntimeError("Original executable changed")
    print(json.dumps({"exe": str(TARGET), "pid": proc.pid,
                      "route_limit_loaded": value, "saves_changed": changed,
                      "original_exe_unchanged": True}))


if __name__ == "__main__":
    main()
