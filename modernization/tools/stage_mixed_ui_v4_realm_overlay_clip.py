"""Stage a reversible native realm overlay clipping fix in isolated v4."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import capstone
import pefile

from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB
from wide169_build import ROOT


SOURCE = '404b7f2dca4c7ddde93cead1d627e657351d3fd277dcb9340aad76bc78adf5ac'
BACKUP = BASE / 'before-realm-overlay-clip'
ENGINE = LAB / 'Chaos-Wide169-engine.exe'
PREVIEW = BASE / 'game/Chaos-Mixed-UI-Preview.exe'
LAUNCHER = ROOT / 'modernization/build/mixed-ui-v4-runtime/launcher.cpp'
MANIFEST = BASE / 'manifest.json'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stage() -> None:
    if BACKUP.exists():
        raise RuntimeError('Overlay clip backup already exists')
    raw = ENGINE.read_bytes()
    if sha(raw) != SOURCE:
        raise RuntimeError('Unknown isolated v4 engine')
    manifest_raw = MANIFEST.read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest['files']['game-wide169/Chaos-Wide169-engine.exe'] != SOURCE:
        raise RuntimeError('V4 manifest engine identity differs')
    preview_raw = PREVIEW.read_bytes()
    if sha(preview_raw) != manifest['files']['game/Chaos-Mixed-UI-Preview.exe']:
        raise RuntimeError('V4 launcher identity differs')
    launcher_raw = LAUNCHER.read_bytes()
    if SOURCE.encode() not in launcher_raw:
        raise RuntimeError('Launcher expected engine hash differs')
    pe = pefile.PE(data=raw)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    output = bytearray(raw)
    sites = [(0x5506d4, 0x5506fc, 'flag-overlay'),
             (0x5509a5, 0x5509cd, 'wizard-and-marker-overlay')]
    changes = []
    # These blocks originally push 480/600 then 640/800 and clear ECX/EDX
    # before 0x57dc60 stores the software sprite clipping rectangle.
    replacement = bytes.fromhex('68a005000068000a000031d231c9')
    for begin, end, label in sites:
        offset = pe.get_offset_from_rva(begin - pe.OPTIONAL_HEADER.ImageBase)
        old = raw[offset:offset + end - begin]
        instructions = list(md.disasm(old, begin))
        if not instructions or instructions[0].address != begin or instructions[-1].address + instructions[-1].size != end:
            raise RuntimeError(f'Unrecognized {label} instruction boundary')
        if not any(i.mnemonic == 'push' for i in instructions) or not any(i.mnemonic == 'xor' for i in instructions):
            raise RuntimeError(f'Unrecognized {label} clip setup')
        output[offset:offset + len(old)] = replacement + b'\x90' * (len(old) - len(replacement))
        changes.append({'site': hex(begin), 'resume': hex(end), 'label': label,
                        'before': old.hex(), 'after': output[offset:offset + len(old)].hex()})
    new_hash = sha(output)
    BACKUP.mkdir()
    shutil.copy2(ENGINE, BACKUP / ENGINE.name)
    shutil.copy2(PREVIEW, BACKUP / PREVIEW.name)
    (BACKUP / 'launcher.cpp').write_bytes(launcher_raw)
    (BACKUP / 'manifest.json').write_bytes(manifest_raw)
    try:
        ENGINE.write_bytes(output)
        LAUNCHER.write_bytes(launcher_raw.replace(SOURCE.encode(), new_hash.encode()))
        runtime = LAUNCHER.parent
        subprocess.run(['cmd', '/c', 'build-candidate.cmd'], cwd=runtime,
                       check=True, timeout=180)
        shutil.copy2(runtime / PREVIEW.name, PREVIEW)
        manifest['files']['game-wide169/Chaos-Wide169-engine.exe'] = new_hash
        manifest['files']['game/Chaos-Mixed-UI-Preview.exe'] = sha(PREVIEW.read_bytes())
        MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    except Exception:
        ENGINE.write_bytes(raw)
        PREVIEW.write_bytes(preview_raw)
        LAUNCHER.write_bytes(launcher_raw)
        MANIFEST.write_bytes(manifest_raw)
        raise
    report = {'status': 'staged-awaiting-baseline-paired-retest',
              'source_sha256': SOURCE, 'engine_sha256': new_hash,
              'launcher_sha256': sha(PREVIEW.read_bytes()), 'patches': changes,
              'rollback': str(BACKUP)}
    (BASE / 'realm-overlay-clip-stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    stage()
