"""Disable native frame skipping in an owned known-build single-player trial."""
import argparse
import ctypes
from ctypes import wintypes
import json
from trace_engine import api, checked_file


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pid", type=int)
    args = ap.parse_args()
    k = api()
    digest = checked_file(k, args.pid)
    k.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k.WriteProcessMemory.argtypes = k.ReadProcessMemory.argtypes
    h = k.OpenProcess(0x1030, False, args.pid)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        count = ctypes.c_size_t()
        before = wintypes.DWORD()
        if not k.ReadProcessMemory(h, 0x5E1418, ctypes.byref(before), 4, ctypes.byref(count)) or count.value != 4:
            raise ctypes.WinError(ctypes.get_last_error())
        if before.value != 1:
            raise RuntimeError(f"Unexpected skip configuration: {before.value}")
        zero = wintypes.DWORD(0)
        if not k.WriteProcessMemory(h, 0x5E1418, ctypes.byref(zero), 4, ctypes.byref(count)) or count.value != 4:
            raise ctypes.WinError(ctypes.get_last_error())
        print(json.dumps({"exe_sha256": digest, "native_max_skip_old": before.value,
                          "native_max_skip_new": 0, "installed_files_modified": False}))
    finally:
        k.CloseHandle(h)


if __name__ == "__main__":
    main()
