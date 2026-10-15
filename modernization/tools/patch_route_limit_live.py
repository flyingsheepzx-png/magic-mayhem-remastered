"""Raise one known-build route search limit in an owned diagnostic process.

This is an A/B experiment, not an installed optimization. The owning harness
terminates the process after the trial and restores the original game files.
"""
import argparse
import ctypes
from ctypes import wintypes
import json

from trace_engine import api, checked_file

ADDRESS = 0x5E174C
EXPECTED = 300


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("value", type=int)
    args = parser.parse_args()
    if not 300 < args.value <= 1200:
        parser.error("Experimental value must be 301..1200")
    kernel = api()
    digest = checked_file(kernel, args.pid)
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                         ctypes.c_void_p, ctypes.c_size_t,
                                         ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL
    kernel.WriteProcessMemory.argtypes = kernel.ReadProcessMemory.argtypes
    kernel.WriteProcessMemory.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000 | 0x10 | 0x20, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        current = wintypes.DWORD()
        written = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, ADDRESS, ctypes.byref(current), 4,
                                        ctypes.byref(written)) or written.value != 4:
            raise ctypes.WinError(ctypes.get_last_error())
        if current.value != EXPECTED:
            raise RuntimeError(f"Unexpected route limit {current.value}; refusing experiment")
        replacement = wintypes.DWORD(args.value)
        if not kernel.WriteProcessMemory(handle, ADDRESS, ctypes.byref(replacement), 4,
                                         ctypes.byref(written)) or written.value != 4:
            raise ctypes.WinError(ctypes.get_last_error())
        print(json.dumps({"exe_sha256": digest, "address": hex(ADDRESS),
                          "old": EXPECTED, "new": args.value,
                          "installed_files_modified": False, "experimental": True}))
    finally:
        kernel.CloseHandle(handle)


if __name__ == "__main__":
    main()
