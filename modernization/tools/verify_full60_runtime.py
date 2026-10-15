"""Short owned launch smoke for the hash-gated installed 30/60 entry."""
import ctypes
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from install_full60 import ROOT, TARGET, LAUNCHER_SHA, no_game_running
from install_full60_main import TARGET as MAIN_TARGET, MAIN_SHA


class ProcessEntry(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]


def processes(kernel):
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    rows = []
    try:
        if kernel.Process32FirstW(handle, ctypes.byref(entry)):
            while True:
                rows.append((entry.th32ProcessID, entry.th32ParentProcessID,
                             entry.szExeFile.lower()))
                if not kernel.Process32NextW(handle, ctypes.byref(entry)):
                    break
    finally:
        kernel.CloseHandle(handle)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", action="store_true", help="Verify the installed Chaos.exe main entry")
    args = parser.parse_args()
    target, expected = (MAIN_TARGET, MAIN_SHA) if args.main else (TARGET, LAUNCHER_SHA)
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise SystemExit("Unknown installed entry")
    no_game_running()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    kernel.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_void_p, ctypes.c_size_t,
                                        ctypes.POINTER(ctypes.c_size_t)]
    kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    launcher = subprocess.Popen([str(target)], cwd=ROOT)
    child = None
    report = {"launcher_pid": launcher.pid, "entry": str(target)}
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            matches = [pid for pid, parent, name in processes(kernel)
                       if parent == launcher.pid and name == "chaos-singleplayer-600.exe"]
            if matches:
                child = matches[0]
                break
            if launcher.poll() is not None:
                raise RuntimeError(f"Launcher exited early: {launcher.returncode}")
            time.sleep(0.2)
        if child is None:
            raise RuntimeError("Hash-verified game child was not started")
        report["game_pid"] = child
        handle = kernel.OpenProcess(0x1011, 0, child)  # query, read, terminate owned child
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            time.sleep(2)
            sites = (0x50fcec, 0x5106da, 0x512460, 0x4fa261, 0x4fa622,
                     0x4fff41, 0x5108c9, 0x4fd552, 0x4fd5a6,
                     0x5104d1, 0x46b488)
            hooks = {}
            for address in sites:
                value = ctypes.c_ubyte()
                count = ctypes.c_size_t()
                okay = kernel.ReadProcessMemory(handle, ctypes.c_void_p(address),
                                                ctypes.byref(value), 1, ctypes.byref(count))
                hooks[f"{address:#x}"] = bool(okay and count.value == 1 and value.value == 0xe9)
            report["hooks"] = hooks
            report["all_hooks_loaded"] = all(hooks.values())
            if not report["all_hooks_loaded"]:
                raise RuntimeError(f"Missing runtime hooks: {hooks}")
        finally:
            kernel.TerminateProcess(handle, 0)
            kernel.CloseHandle(handle)
    finally:
        if launcher.poll() is None:
            try:
                launcher.wait(timeout=5)
            except subprocess.TimeoutExpired:
                launcher.terminate()
                launcher.wait(timeout=5)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
