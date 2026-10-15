"""Run the normal budgeted route action as soon as a cell-safe order is set.

Owned known-build process only. This does not replace route buffers or clear
movement gates. The native action retains eligibility, budgets, continuation,
passability and occupancy management. It is an experiment, not a shipped fix.
"""
import argparse
import ctypes
from ctypes import wintypes
import json

from patch_direct_route_live import rel32, SITE, ORIGINAL, RETURN
from trace_engine import api, checked_file


def code_at(base):
    code = bytearray.fromhex("9c603b3558ef6d00750083be18060000007500")
    skips = [9, 18]
    code.extend(bytes.fromhex("8bce"))
    code.append(0xE8)
    code.extend(rel32(base + len(code) + 4, 0x519AE0))
    end = len(code)
    for offset in skips:
        code[offset] = end - offset - 1
    code.extend(bytes.fromhex("619d"))
    code.extend(ORIGINAL)
    code.append(0xE9)
    code.extend(rel32(base + len(code) + 4, RETURN))
    return bytes(code)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pid", type=int)
    args = ap.parse_args()
    k = api()
    digest = checked_file(k, args.pid)
    k.VirtualAllocEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                 wintypes.DWORD, wintypes.DWORD]
    k.VirtualAllocEx.restype = ctypes.c_void_p
    k.VirtualProtectEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                   wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    k.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k.WriteProcessMemory.argtypes = k.ReadProcessMemory.argtypes
    k.FlushInstructionCache.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t]
    h = k.OpenProcess(0x1038, False, args.pid)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        count = ctypes.c_size_t()
        old = ctypes.create_string_buffer(len(ORIGINAL))
        if not k.ReadProcessMemory(h, SITE, old, len(ORIGINAL), ctypes.byref(count)):
            raise ctypes.WinError(ctypes.get_last_error())
        if old.raw != ORIGINAL:
            raise RuntimeError("Unexpected order exit; refusing detour")
        address = k.VirtualAllocEx(h, None, 4096, 0x3000, 0x40)
        if not address or address >= 0x100000000:
            raise RuntimeError("No x86 trampoline allocation")
        code = code_at(address)
        if not k.WriteProcessMemory(h, address, ctypes.create_string_buffer(code), len(code), ctypes.byref(count)) or count.value != len(code):
            raise ctypes.WinError(ctypes.get_last_error())
        patch = b"\xe9" + rel32(SITE + 5, address) + b"\x90"
        protection = wintypes.DWORD()
        if not k.VirtualProtectEx(h, SITE, len(patch), 0x40, ctypes.byref(protection)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not k.WriteProcessMemory(h, SITE, ctypes.create_string_buffer(patch), len(patch), ctypes.byref(count)) or count.value != len(patch):
                raise ctypes.WinError(ctypes.get_last_error())
            k.FlushInstructionCache(h, SITE, len(patch))
        finally:
            ignored = wintypes.DWORD()
            k.VirtualProtectEx(h, SITE, len(patch), protection.value, ctypes.byref(ignored))
        print(json.dumps({"exe_sha256": digest, "pid": args.pid, "site": hex(SITE),
                          "trampoline": hex(address), "unit0_only": True,
                          "native_budgeted_action": True, "requires_motion_gate_zero": True,
                          "installed_file_modified": False, "experimental": True}))
    finally:
        k.CloseHandle(h)


if __name__ == "__main__":
    main()
