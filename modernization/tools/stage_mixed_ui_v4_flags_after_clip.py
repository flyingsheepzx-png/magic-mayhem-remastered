"""Stage verified Qwen flag frames after the native overlay clip repair."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB


REL = 'Interface/RealmViewer/Generic/flags.spr'
ORIGINAL = 'a57cb4a5bfb07e4a6108028c0b1538c069637eeaec775a967b08922824d1cb3c'
QWEN = '615dab4f7cda7887c4497df8093cbfbf331ad80631c8459f4f0e1e46ad66a547'
ENGINE = '3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stage() -> None:
    original = LAB / REL
    derivative = BASE / 'sprite-derivatives-flags' / REL
    backup = BASE / 'before-realm-flags-after-clip'
    if backup.exists():
        raise RuntimeError('Flag backup already exists')
    if sha(original.read_bytes()) != ORIGINAL or sha(derivative.read_bytes()) != QWEN:
        raise RuntimeError('Flag source or Qwen derivative changed')
    manifest_path = BASE / 'manifest.json'
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest['files']['game-wide169/Chaos-Wide169-engine.exe'] != ENGINE or \
       manifest['files']['game-wide169/' + REL] != ORIGINAL:
        raise RuntimeError('Isolated package identity differs')
    prior = json.loads((BASE / 'realm-flags-stage.json').read_text(encoding='utf-8'))
    if prior['file']['sha256'] != QWEN or prior['file']['source_sha256'] != ORIGINAL or prior['file']['frames'] != 89:
        raise RuntimeError('Prior Qwen validation differs')
    saved = backup / REL
    saved.parent.mkdir(parents=True)
    saved.write_bytes(original.read_bytes())
    (backup / 'manifest.json').write_bytes(manifest_raw)
    try:
        original.write_bytes(derivative.read_bytes())
        manifest['files']['game-wide169/' + REL] = QWEN
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    except Exception:
        original.write_bytes(saved.read_bytes())
        manifest_path.write_bytes(manifest_raw)
        raise
    report = {'status': 'staged-awaiting-paired-retest', 'asset': REL,
              'source_sha256': ORIGINAL, 'qwen_sha256': QWEN,
              'engine_sha256': ENGINE, 'rollback': str(saved)}
    (BASE / 'realm-flags-after-clip-stage.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    stage()
