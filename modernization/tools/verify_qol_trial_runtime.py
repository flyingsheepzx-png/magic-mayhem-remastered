"""Bounded owned-process smoke for the isolated QoL trial modules."""

import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import time

from install_qol_trial import ROOT, TARGET, SOURCE, no_game_running, sha
from verify_full60_runtime import ProcessEntry, processes


def main():
    if sha(TARGET) != sha(SOURCE):
        raise RuntimeError("Unknown QoL trial launcher")
    no_game_running()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.TerminateProcess.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    launcher = subprocess.Popen([str(TARGET)], cwd=ROOT)
    child = None
    report = {"launcher_pid": launcher.pid}
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            matches = [pid for pid, parent, name in processes(kernel)
                       if parent == launcher.pid and name == "chaos-singleplayer-600.exe"]
            if matches:
                child = matches[0]
                break
            if launcher.poll() is not None:
                raise RuntimeError(f"Trial launcher exited early: {launcher.returncode}")
            time.sleep(0.2)
        if child is None:
            raise RuntimeError("No owned engine child")
        report["game_pid"] = child
        handle = kernel.OpenProcess(0x1011, False, child)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            time.sleep(2)
            sites = (0x50fcec, 0x5106da, 0x512460, 0x4fa261, 0x4fa622,
                     0x4fff41, 0x5108c9, 0x4fd552, 0x4fd5a6,
                     0x5104d1, 0x46b488, 0x578610)
            hooks = {}
            for address in sites:
                value = ctypes.c_ubyte()
                count = ctypes.c_size_t()
                good = kernel.ReadProcessMemory(handle, ctypes.c_void_p(address),
                                                ctypes.byref(value), 1, ctypes.byref(count))
                hooks[f"{address:#x}"] = bool(good and count.value == 1 and value.value == 0xE9)
            report["hooks"] = hooks
            report["all_hooks_loaded"] = all(hooks.values())
            if not report["all_hooks_loaded"]:
                raise RuntimeError(f"Trial hook missing: {hooks}")
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
