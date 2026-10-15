"""Install only three reviewed plain Portmanteau Buttons frames in v4."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

from PIL import ImageChops

from compare_hd_baseline import baseline_identity, sha
from spr_assets import read_spr, decode
from wide169_build import ROOT


BASE = ROOT / 'modernization/playtests/mixed-ui-v4'
REL = 'Sprites/Buttons.spr'
AUDIT = ROOT / 'modernization/assets/hd/qwen-value-audits/1790676679178214200'
TARGETS = {0, 3, 9}
EXPECTED = 'a1ae2ec738f924439d8d85b3ee8153244355cc2bb82c03844210bb49c0dcdaa3'


def main():
    baseline_identity()
    target = BASE / 'game-wide169' / REL
    manifest_path = BASE / 'manifest.json'
    old = target.read_bytes()
    manifest_old = manifest_path.read_bytes()
    manifest = json.loads(manifest_old)
    key = 'game-wide169/' + REL
    if sha(target) != EXPECTED or manifest['files'][key] != EXPECTED:
        raise RuntimeError('Unknown v4 Buttons source')
    if any(sha(BASE / name) != digest for name, digest in manifest['files'].items()):
        raise RuntimeError('v4 manifest mismatch')
    audit = json.loads((AUDIT / 'audit.json').read_text(encoding='utf-8'))
    if audit['verdict'] != 'plain enlargement wins' or audit['qwen_runtime_sha256'] != EXPECTED:
        raise RuntimeError('Unreviewed asset verdict')
    plain_path = AUDIT / 'plain-buttons.spr'
    if sha(plain_path) != audit['plain_runtime_sha256']:
        raise RuntimeError('Plain comparison payload changed')
    qpal, qframes = read_spr(target)
    ppal, pframes = read_spr(plain_path)
    if qpal or ppal or len(qframes) != 21 or len(pframes) != 21:
        raise RuntimeError('Unexpected Buttons container')
    payloads = []
    for before, after in zip(qframes, pframes):
        if before['index'] in TARGETS:
            if (before['width'], before['height'], before['offset'], before['name']) != (
                    after['width'], after['height'], after['offset'], after['name']):
                raise RuntimeError('Plain frame geometry differs')
            if ImageChops.difference(decode(qpal, before).getchannel('A'),
                                     decode(ppal, after).getchannel('A')).getbbox():
                raise RuntimeError('Plain frame coverage differs')
            payloads.append(after['data'])
        else:
            payloads.append(before['data'])
    output = bytearray(old[:24])
    offset = 0
    for data in payloads:
        output.extend(struct.pack('<I', offset))
        offset += len(data)
    for data in payloads:
        output.extend(data)
    struct.pack_into('<I', output, 4, len(output))
    backup = BASE / 'before-plain-port-buttons-20260929'
    if backup.exists():
        raise RuntimeError('Backup already exists')
    backup.mkdir()
    (backup / 'Buttons.spr').write_bytes(old)
    (backup / 'manifest.json').write_bytes(manifest_old)
    try:
        target.write_bytes(output)
        new_sha = hashlib.sha256(output).hexdigest()
        manifest['files'][key] = new_sha
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        _, check = read_spr(target)
        if len(check) != 21 or any(check[i]['data'] != payloads[i] for i in range(21)):
            raise RuntimeError('Staged SPR roundtrip failed')
        if any(sha(BASE / name) != digest for name, digest in manifest['files'].items()):
            raise RuntimeError('Staged v4 manifest mismatch')
    except Exception:
        target.write_bytes(old)
        manifest_path.write_bytes(manifest_old)
        raise
    report = {'source': REL, 'source_sha256': EXPECTED, 'sha256': new_sha,
              'frames_plain': sorted(TARGETS), 'frames_unchanged': 18,
              'audit': str(AUDIT), 'backup': str(backup)}
    (BASE / 'plain-port-buttons-stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
