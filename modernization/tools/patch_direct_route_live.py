"""Experimental unit0-only route dispatch at explicit-order handler exit.

Known Chaos.exe only. Allocates one remote trampoline and changes six live code
bytes. The process is owned by the diagnostic harness and terminated afterward;
installed executable bytes are never changed. Do not use in multiplayer.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import struct

from trace_engine import api, checked_file, SUPPORTED

SITE = 0x50FCEC
ORIGINAL = bytes.fromhex("8b8ee8060000")
ROUTE = 0x512800
RETURN = SITE + len(ORIGINAL)


def rel32(from_after: int, target: int) -> bytes:
    return struct.pack("<I", (target - from_after) & 0xFFFFFFFF)


def code_at(base: int, all_orders: bool = False) -> bytes:
    code = bytearray()
    def add(hex_bytes):
        code.extend(bytes.fromhex(hex_bytes))
    add("9c60")  # preserve flags and all general registers
    add("3b3558ef6d00")  # cmp esi,[unit0 table]
    code.extend(b"\x75\x00")
    first_skip = len(code) - 1
    second_skip = None
    if not all_orders:
        add("83be1806000000")  # cmp [esi+0x618],0
        code.extend(b"\x74\x00")
        second_skip = len(code) - 1
    add("8b869406000050")  # push [esi+0x694] (via eax)
    add("8b867309000050")  # push target z
    add("8b866f09000050")  # push target y
    add("8b866b09000050")  # push target x
    add("8bce")            # thiscall unit
    code.append(0xE8)
    code.extend(rel32(base + len(code) + 4, ROUTE))
    skip = len(code)
    code[first_skip] = (skip - first_skip - 1) & 0xFF
    if second_skip is not None:
        code[second_skip] = (skip - second_skip - 1) & 0xFF
    add("619d")  # restore registers and flags
    code.extend(ORIGINAL)
    code.append(0xE9)
    code.extend(rel32(base + len(code) + 4, RETURN))
    return bytes(code)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pid", type=int)
    ap.add_argument("--all-orders", action="store_true",
                    help="Experimental synchronous route dispatch for either order branch")
    args = ap.parse_args()
    kernel = api()
    checked_file(kernel, args.pid)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.VirtualAllocEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                      wintypes.DWORD, wintypes.DWORD]
    kernel.VirtualAllocEx.restype = ctypes.c_void_p
    kernel.VirtualProtectEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.VirtualProtectEx.restype = wintypes.BOOL
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL
    kernel.WriteProcessMemory.argtypes = kernel.ReadProcessMemory.argtypes
    kernel.WriteProcessMemory.restype = wintypes.BOOL
    kernel.FlushInstructionCache.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t]
    kernel.FlushInstructionCache.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000 | 0x0010 | 0x0020 | 0x0008, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        current = (ctypes.c_ubyte * len(ORIGINAL))()
        done = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, SITE, current, len(current), ctypes.byref(done)):
            raise ctypes.WinError(ctypes.get_last_error())
        if bytes(current) != ORIGINAL:
            raise RuntimeError("Unexpected route-order site; refusing trampoline")
        remote = kernel.VirtualAllocEx(handle, None, 4096, 0x3000, 0x40)
        if not remote or remote >= 0x100000000:
            raise RuntimeError("Could not allocate x86 trampoline")
        code = code_at(remote, args.all_orders)
        written = ctypes.c_size_t()
        buffer = ctypes.create_string_buffer(code)
        if not kernel.WriteProcessMemory(handle, remote, buffer, len(code),
                                         ctypes.byref(written)) or written.value != len(code):
            raise ctypes.WinError(ctypes.get_last_error())
        patch = b"\xe9" + rel32(SITE + 5, remote) + b"\x90"
        old = wintypes.DWORD()
        if not kernel.VirtualProtectEx(handle, SITE, len(patch), 0x40, ctypes.byref(old)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            data = ctypes.create_string_buffer(patch)
            if not kernel.WriteProcessMemory(handle, SITE, data, len(patch),
                                             ctypes.byref(written)) or written.value != len(patch):
                raise ctypes.WinError(ctypes.get_last_error())
            kernel.FlushInstructionCache(handle, SITE, len(patch))
        finally:
            discard = wintypes.DWORD()
            kernel.VirtualProtectEx(handle, SITE, len(patch), old.value,
                                    ctypes.byref(discard))
        print(json.dumps({"exe_sha256": SUPPORTED, "pid": args.pid,
                          "site": hex(SITE), "trampoline": hex(remote),
                          "unit0_only": True, "installed_file_modified": False,
                          "all_orders": args.all_orders,
                          "experimental": True}))
    finally:
        kernel.CloseHandle(handle)


if __name__ == "__main__":
    main()
