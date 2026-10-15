"""Read-only input state for this game's hash-verified community engine child."""

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import struct

ROOT = (Path(__file__).resolve().parents[2] / "game")
HASHES = {"Chaos-singleplayer-600.exe": "856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd",
          "Chaos-HD60-engine.exe": "be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7"}


def snapshot(pid):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1010, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        path = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(32768)
        if not kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        image = Path(path.value)
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if image.name not in HASHES or digest != HASHES[image.name]:
            raise RuntimeError("Unknown game image; address sampling refused")
        def read(address, size):
            buffer = ctypes.create_string_buffer(size)
            count = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(count)) or count.value != size:
                raise RuntimeError(f"Cannot read {address:#x}")
            return buffer.raw
        def integer(address):
            return struct.unpack("<i", read(address, 4))[0]
        result = {"pid": pid, "engine_sha256": digest,
                  "scene": integer(0x6e1f68), "players": integer(0x6e1f0c),
                  "selected_count": integer(0x6e984c),
                  "cursor_id": integer(0x5e04c8),
                  "cursor_draw_top_left": [integer(0x641aa0), integer(0x641aa4)],
                  "surface": [integer(0x6a49f0), integer(0x6a49f4)],
                  "view_mode_a": integer(0x6cbb70), "view_mode_s": integer(0x6e1f28)}
        if image.name == 'Chaos-HD60-engine.exe':
            result['spellbox'] = {'owner': integer(0x6a2dd0+0x18ec),
                'icon_count': integer(0x6a2dd0+0x1518),
                'active_icon': integer(0x6a2dd0+0x1908),
                'target_mode': integer(0x689920)}
            result['input_mode'] = integer(0x6903e8)
            control=integer(0x642034)
            result['world_control']={'pointer':control,'handler':integer(integer(control))} if control>0x10000 else None
            result['icons']=[{'rect':list(struct.unpack('<4i',read(0x6a2dd0+0xfc+i*0xc6+0x11,16))),
                'sound':integer(0x6a2dd0+0xfc+i*0xc6+0x51),
                'handler':integer(integer(0x6a2dd0+0xfc+i*0xc6))} for i in range(max(0,min(26,integer(0x6a2dd0+0x1518))))]
            result['unit_count']=integer(0x6df180)
        table, count = integer(0x6def58), integer(0x6def5c)
        if table >= 0x10000 and 0 < count <= 4096:
            active_count=integer(0x6df180)
            if 0 <= active_count <= count:
                result['units']=[{'index':i,'id':integer(table+i*0xe4b),
                    'type':integer(integer(table+i*0xe4b+0xac)),
                    'owner':integer(table+i*0xe4b+0x174),
                    'selected':integer(table+i*0xe4b+0x68)}
                    for i in range(active_count) if integer(table+i*0xe4b+4)]
            result["unit0"] = {"selection": integer(table+0x68),
                               "group": integer(table+0x8e9),
                               "grid": [integer(table+8),integer(table+12),integer(table+16)],
                               "world": [integer(table+0x14),integer(table+0x18)]}
            result['unit0']['pending_spell_index'] = integer(table+0x5e8)
            result['unit0']['spell_count'] = integer(table+0x56c)
        return result
    finally:
        kernel.CloseHandle(handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    args = parser.parse_args()
    print(json.dumps(snapshot(args.pid)))
