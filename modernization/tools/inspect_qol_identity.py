"""Read-only, hash-gated snapshot of Portmanteau and battle spell identities."""
import ctypes
import hashlib
import json
import struct
from pathlib import Path
from qol_telemetry import snapshot
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qol_identity import native_layout, equipped_slot_spells, battle_slot_icons
from pathlib import Path
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / 'game'
STATE = ROOT / 'modernization/logs/hd-qol-background-session.json'
EXPECTED = 'be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7'
assert hashlib.sha256((GAME / 'Chaos-HD60-engine.exe').read_bytes()).hexdigest() == EXPECTED
session = json.loads(STATE.read_text())
assert not session.get('restored')
pid = session['pid']
snapshot(pid)  # Verify the live process image, not just the installed file.
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k.OpenProcess.restype = wintypes.HANDLE
k.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k.ReadProcessMemory.restype = wintypes.BOOL
k.CloseHandle.argtypes = [wintypes.HANDLE]
h = k.OpenProcess(0x1010, False, pid)
if not h:
    raise OSError(ctypes.get_last_error())

def read(addr, count):
    buf = ctypes.create_string_buffer(count)
    got = ctypes.c_size_t()
    if not k.ReadProcessMemory(h, addr, buf, count, ctypes.byref(got)) or got.value != count:
        raise RuntimeError(f'short read at {addr:#x}')
    return buf.raw

def d(addr):
    return struct.unpack('<I', read(addr, 4))[0]

try:
    result = {'pid': pid, 'engine_sha256': EXPECTED}
    result['talisman_spell_table'] = [list(struct.unpack('<3i', read(0x6f4c08 + i*12, 12))) for i in range(25)]
    player = 0x65b250
    result['campaign_player'] = {'address': player,
        'tray_counts': [d(player + 0xf0 + i*4) for i in range(3)],
        'owned_items': list(struct.unpack('<25i', read(player + 0x8c, 100)))}
    equipped_count = d(player + 0x92a)
    if 0 <= equipped_count <= 63:
        equipped_ptr = d(player + 0x932)
        result['campaign_player']['equipped_spells'] = list(struct.unpack(
            '<' + 'i'*equipped_count, read(equipped_ptr, equipped_count*4))) if equipped_count else []
    ui = 0x6f2aa0
    counts = [d(ui + 0x84 + t * 4) for t in range(3)]
    if all(0 <= n <= 21 for n in counts):
        result['portmanteau'] = {'counts': counts, 'owner': d(ui + 0x90), 'slots': []}
        for t, n in enumerate(counts):
            controls = d(ui + 0x218 + t * 4)
            if not controls:
                continue
            for i in range(n):
                result['portmanteau']['slots'].append({
                    'tray': t, 'slot': i,
                    'spell': d(ui + 0xb4 + t * 0x54 + i * 4),
                    'control': controls + i * 0x86,
                    'control_spell': d(controls + i * 0x86 + 0x7e),
                })
    box = 0x6a2dd0
    count = d(box + 0x1518)
    owner = d(box + 0x18ec)
    result['battle'] = {'owner': owner, 'count': count, 'icons': []}
    if 0 <= count <= 26 and owner:
        definition = d(owner+0xac)
        result['battle']['unit_type'] = d(definition) if definition else None
        result['battle']['unit_player'] = d(owner+0x7c)
        spell_count = d(owner + 0x56c)
        if 0 <= spell_count <= 26:
            result['battle']['unit_spells'] = [d(owner + 0x570 + i*4) for i in range(spell_count)]
        for i in range(count):
            b = box + 0xfc + i*0xc6
            result['battle']['icons'].append({
                'index': i, 'spell': d(b+0xb5), 'type': d(b+0xb9),
                'source_ptr': d(b+0x59), 'aux_ptr': d(b+0x35),
                'extra': d(b+0xbd), 'state': d(b+0xc1),
                'rect': [d(b+o) for o in (0x11,0x15,0x19,0x1d)],
            })
    player_data = result['campaign_player']
    if 'equipped_spells' in player_data:
        layout = native_layout(player_data['tray_counts'], player_data['equipped_spells'],
                               player_data['owned_items'], result['talisman_spell_table'])
        result['reconstructed_layout'] = layout
        spells = equipped_slot_spells(layout, result['talisman_spell_table'])
        result['unique_slot_icons'] = [
            {'tray': slot[0], 'slot': slot[1], 'icon': icon, 'spell': spells[slot]}
            for slot, icon in battle_slot_icons(spells, result['battle']['icons']).items()]
    print(json.dumps(result, indent=2))
finally:
    k.CloseHandle(h)
