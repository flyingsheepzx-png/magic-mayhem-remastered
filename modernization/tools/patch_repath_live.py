"""Experimental known-build route-order fast path in an owned process only.

This applies two one-byte conditional-to-unconditional branches. It does not
modify Chaos.exe on disk. Validation must prove legality and save compatibility
before this can become an installed feature.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys

from trace_engine import ROOT, SUPPORTED, api, checked_file

PATCHES = ((0x50FC47, b"\x74", b"\xeb"),  # process a new order during movement
           (0x50AA65, b"\x74", b"\xeb"))  # dispatch that order despite +0x618


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    kernel = api()
    checked_file(kernel, args.pid)
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                         ctypes.c_void_p, ctypes.c_size_t,
                                         ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL
    kernel.WriteProcessMemory.argtypes = kernel.ReadProcessMemory.argtypes
    kernel.WriteProcessMemory.restype = wintypes.BOOL
    kernel.VirtualProtectEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                        ctypes.c_size_t, wintypes.DWORD,
                                        ctypes.POINTER(wintypes.DWORD)]
    kernel.VirtualProtectEx.restype = wintypes.BOOL
    kernel.FlushInstructionCache.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                              ctypes.c_size_t]
    kernel.FlushInstructionCache.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000 | 0x0010 | 0x0020 | 0x0008, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        def read(address):
            value = ctypes.c_ubyte()
            done = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle, address, ctypes.byref(value), 1,
                                            ctypes.byref(done)) or done.value != 1:
                raise ctypes.WinError(ctypes.get_last_error())
            return bytes((value.value,))
        desired = [(address, new if args.restore else old,
                    old if args.restore else new) for address, old, new in PATCHES]
        for address, expected, _ in desired:
            if read(address) != expected:
                raise RuntimeError(f"Unexpected code at 0x{address:08x}; refusing patch")
        changed = []
        try:
            for address, expected, replacement in desired:
                previous = wintypes.DWORD()
                if not kernel.VirtualProtectEx(handle, address, 1, 0x40,
                                               ctypes.byref(previous)):
                    raise ctypes.WinError(ctypes.get_last_error())
                try:
                    written = ctypes.c_size_t()
                    value = ctypes.c_ubyte(replacement[0])
                    if not kernel.WriteProcessMemory(handle, address, ctypes.byref(value), 1,
                                                     ctypes.byref(written)) or written.value != 1:
                        raise ctypes.WinError(ctypes.get_last_error())
                    kernel.FlushInstructionCache(handle, address, 1)
                    if read(address) != replacement:
                        raise RuntimeError("Patch verification failed")
                    changed.append((address, expected))
                finally:
                    discarded = wintypes.DWORD()
                    kernel.VirtualProtectEx(handle, address, 1, previous.value,
                                            ctypes.byref(discarded))
        except Exception:
            for address, previous_byte in reversed(changed):
                old_protection = wintypes.DWORD()
                kernel.VirtualProtectEx(handle, address, 1, 0x40,
                                        ctypes.byref(old_protection))
                value = ctypes.c_ubyte(previous_byte[0])
                done = ctypes.c_size_t()
                kernel.WriteProcessMemory(handle, address, ctypes.byref(value), 1,
                                          ctypes.byref(done))
                kernel.FlushInstructionCache(handle, address, 1)
                discarded = wintypes.DWORD()
                kernel.VirtualProtectEx(handle, address, 1, old_protection.value,
                                        ctypes.byref(discarded))
            raise
        print(json.dumps({"exe_sha256": SUPPORTED, "pid": args.pid,
                          "active": not args.restore,
                          "sites": [hex(address) for address, _, _ in desired],
                          "installed_file_modified": False}))
    finally:
        kernel.CloseHandle(handle)


if __name__ == "__main__":
    main()
