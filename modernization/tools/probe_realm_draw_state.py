"""Read-only, hash-gated realm object probe in owned comparison sessions."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import argparse
import hashlib
import json
from pathlib import Path
import time

from compare_hd_baseline import CaptureSession
from wide169_build import ROOT


class MemoryBasicInformation(ctypes.Structure):
    _fields_ = [('base', ctypes.c_void_p), ('allocation_base', ctypes.c_void_p),
                ('allocation_protect', W.DWORD), ('padding', W.DWORD),
                ('size', ctypes.c_size_t), ('state', W.DWORD),
                ('protect', W.DWORD), ('type', W.DWORD), ('padding2', W.DWORD)]


def find_realm_objects(session):
    kernel = session.k
    kernel.VirtualQueryEx.argtypes = [W.HANDLE, ctypes.c_void_p,
                                      ctypes.POINTER(MemoryBasicInformation), ctypes.c_size_t]
    kernel.VirtualQueryEx.restype = ctypes.c_size_t
    kernel.ReadProcessMemory.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = W.BOOL
    signature = (0x5c6a60).to_bytes(4, 'little')
    candidates = []
    address = 0x10000
    scanned = 0
    while address < 0x80000000 and scanned < 256 * 1024 * 1024:
        region = MemoryBasicInformation()
        if not kernel.VirtualQueryEx(session.handle, address, ctypes.byref(region), ctypes.sizeof(region)):
            break
        start = int(region.base)
        end = start + int(region.size)
        if end <= address:
            break
        if region.state == 0x1000 and region.protect & 0xff in (2, 4, 8, 0x20, 0x40, 0x80):
            for block in range(start, end, 0x10000):
                n = min(0x10000, end - block)
                buf = ctypes.create_string_buffer(n)
                got = ctypes.c_size_t()
                if not kernel.ReadProcessMemory(session.handle, block, buf, n, ctypes.byref(got)) or got.value != n:
                    continue
                scanned += n
                data = buf.raw
                at = data.find(signature)
                while at >= 0:
                    ptr = block + at
                    if ptr % 4 == 0:
                        try:
                            count = session.i(ptr + 0x823)
                            sprite = session.i(ptr + 0x9f)
                            state = session.i(ptr + 0xa2b)
                            row = {'object': hex(ptr), 'flag_count': count,
                                   'flag_sprite': hex(sprite), 'page_state': state}
                            if 0 < count < 100 and 0x10000 < sprite < 0x80000000:
                                flags = session.i(ptr + 0x16)
                                anim = session.i(ptr + 0x1d7)
                                row.update(flag_records=hex(flags), animations=hex(anim),
                                           sprite_frames=session.i(sprite + 0xc),
                                           active_group=session.i(0x659f51),
                                           marker_count=session.i(0x659f55),
                                           spectator=session.i(0x6e0080))
                                if all(0x10000 < p < 0x80000000 for p in (flags, anim)):
                                    row['entries'] = []
                                    for i in range(count):
                                        animation = session.i(anim + i * 0x30 + 4)
                                        item = {'index': i,
                                                'x': session.i(flags + i * 0x8c + 8),
                                                'y': session.i(flags + i * 0x8c + 12),
                                                'animation': hex(animation),
                                                'group': session.i(0x65b1dd + i * 4),
                                                'visibility': session.i(ptr + 0x1e3 + i * 0x50)}
                                        if 0x10000 < animation < 0x80000000:
                                            item.update(frame=session.i(animation + 4),
                                                        offset_x=session.i(animation + 8),
                                                        offset_y=session.i(animation + 12))
                                        row['entries'].append(item)
                            candidates.append(row)
                        except Exception:
                            pass
                    at = data.find(signature, at + 4)
        address = end
    return {'scanned_bytes': scanned, 'candidates': candidates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hd-only', action='store_true',
                        help='probe only manifest-verified isolated v4 during baseline maintenance')
    args = parser.parse_args()
    out = ROOT / 'modernization/assets/hd/realm-draw-probes' / str(time.time_ns())
    out.mkdir(parents=True)
    result = {}
    ctypes.windll.user32.SetProcessDPIAware()
    for label in (('hd',) if args.hd_only else ('baseline', 'hd')):
        fixture = ROOT / ('modernization/playtests/mixed-ui-v4/game-wide169/Save/test5.sav'
                          if label == 'hd' else 'game-wide169/Save/test5.sav')
        staged = False
        if label == 'hd' and not fixture.exists():
            source = ROOT / 'modernization/playtests/mixed-ui-v3/game-wide169/Save/test5.sav'
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != '2b00d8425eb01bb913b7b380f30f18f4e3d1948a0c05168c022819fca7205b7b':
                raise RuntimeError('Unknown test5 fixture')
            fixture.write_bytes(data)
            staged = True
        try:
            with CaptureSession(label, out, 'mixed-ui-v4', verify_baseline=not args.hd_only) as session:
                session.load_fixture('test5', False)
                session.shot('realm-test5')
                result[label] = find_realm_objects(session)
        finally:
            if staged and fixture.exists():
                if hashlib.sha256(fixture.read_bytes()).hexdigest() != '2b00d8425eb01bb913b7b380f30f18f4e3d1948a0c05168c022819fca7205b7b':
                    raise RuntimeError('Temporary fixture changed; retaining for inspection')
                fixture.unlink()
    (out / 'realm-state.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(out)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
