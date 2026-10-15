"""Compare the actual Portmanteau Buttons icons against plain 2x in the game."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import time

from PIL import Image

from compare_hd_baseline import baseline_identity, capture_flow, sha
from spr_assets import read_spr, decode
from stage_mixed_ui_v3_sprites import encode
from wide169_build import ROOT


PACKAGE = ROOT / 'modernization/playtests/mixed-ui-v4'
REL = 'Sprites/Buttons.spr'
SOURCE = ROOT / 'modernization/assets/hd/source-original' / REL
EXPECTED = 'a1ae2ec738f924439d8d85b3ee8153244355cc2bb82c03844210bb49c0dcdaa3'
SOURCE_HASH = '14bc9f870348b8e3df556628de28f5b751748803ba98fc90a6514c7ede47ae23'


def plain_variant(out):
    palettes, frames = read_spr(SOURCE)
    if len(frames) != 21 or sha(SOURCE) != SOURCE_HASH:
        raise RuntimeError('Unknown original icon frames')
    encoded = []
    for frame in frames:
        if frame['width'] and frame['height']:
            original = decode(palettes, frame)
            size = (frame['width'] * 2, frame['height'] * 2)
            image = original.resize(size, Image.Resampling.LANCZOS)
            image.putalpha(original.getchannel('A').resize(size, Image.Resampling.NEAREST))
            encoded.append(encode(frame, image))
        else:
            encoded.append(encode(frame, Image.new('RGBA', (0, 0))))
    raw = bytearray(SOURCE.read_bytes()[:24])
    struct.pack_into('<II', raw, 16, 0, 0)
    position = 0
    for data in encoded:
        raw.extend(struct.pack('<I', position))
        position += len(data)
    for data in encoded:
        raw.extend(data)
    struct.pack_into('<I', raw, 4, len(raw))
    output = out / 'plain-buttons.spr'
    output.write_bytes(raw)
    new_palettes, new_frames = read_spr(output)
    if new_palettes or len(new_frames) != len(frames):
        raise RuntimeError('Plain SPR roundtrip failed')
    for before, after in zip(frames, new_frames):
        if (after['offset'] != [v * 2 for v in before['offset']]
                or [after['width'], after['height']] != [before['width'] * 2, before['height'] * 2]):
            raise RuntimeError('Scaled icon geometry mismatch')
    return bytes(raw)


def checked_capture(label, directory, suffix):
    session = capture_flow(label, directory, 'portmanteau', 'mixed-ui-v4')
    report = json.loads((directory / label / 'capture.json').read_text(encoding='utf-8'))
    if not report.get('restored') or report.get('error'):
        raise RuntimeError('Session rollback failed: ' + suffix)
    if not report.get('checks', {}).get('portmanteau_arrived'):
        raise RuntimeError('Portmanteau did not open: ' + suffix)
    return Path(session.records['portmanteau-after-tutorial']['output'])


def main():
    baseline_identity()
    manifest_path = PACKAGE / 'manifest.json'
    target = PACKAGE / 'game-wide169' / REL
    original_asset = target.read_bytes()
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    key = 'game-wide169/' + REL
    if sha(target) != EXPECTED or manifest['files'].get(key) != EXPECTED:
        raise RuntimeError('Unknown Qwen Buttons candidate')
    if any(sha(PACKAGE / name) != digest for name, digest in manifest['files'].items()):
        raise RuntimeError('Candidate manifest mismatch')
    out = ROOT / 'modernization/assets/hd/qwen-value-audits' / str(time.time_ns())
    out.mkdir(parents=True)
    for name in ('baseline-run', 'qwen-run', 'plain-run'):
        (out / name).mkdir()
    (out / 'rollback-buttons.spr').write_bytes(original_asset)
    (out / 'rollback-manifest.json').write_bytes(original_manifest)
    plain = plain_variant(out)
    try:
        baseline = checked_capture('baseline', out / 'baseline-run', 'baseline')
        qwen = checked_capture('hd', out / 'qwen-run', 'qwen')
        target.write_bytes(plain)
        manifest['files'][key] = hashlib.sha256(plain).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        normal = checked_capture('hd', out / 'plain-run', 'plain')
    finally:
        target.write_bytes(original_asset)
        manifest_path.write_bytes(original_manifest)
    if target.read_bytes() != original_asset or manifest_path.read_bytes() != original_manifest:
        raise RuntimeError('Icon rollback failed')
    if any(sha(PACKAGE / name) != digest for name, digest in
           json.loads(original_manifest)['files'].items()):
        raise RuntimeError('Candidate package changed after rollback')
    with Image.open(baseline) as b, Image.open(qwen) as q, Image.open(normal) as p:
        triple = Image.new('RGB', (7680, 1440))
        for index, opened in enumerate((b, q, p)):
            triple.paste(opened.convert('RGB'), (index * 2560, 0))
        triple.save(out / 'portmanteau-baseline-qwen-plain-7680x1440.png')
        box = (1770, 0, 2240, 220)
        crop = Image.new('RGB', ((box[2]-box[0])*3, box[3]-box[1]))
        for index, opened in enumerate((b, q, p)):
            crop.paste(opened.convert('RGB').crop(box), ((box[2]-box[0])*index, 0))
        crop.save(out / 'top-icons-baseline-qwen-plain.png')
        if q.convert('RGB').tobytes() == p.convert('RGB').tobytes():
            raise RuntimeError('Qwen and plain captures are pixel-identical; page-specific hook did not apply')
    report = {
        'source': REL, 'source_sha256': SOURCE_HASH,
        'qwen_runtime_sha256': EXPECTED,
        'plain_runtime_sha256': hashlib.sha256(plain).hexdigest(),
        'plain_method': 'Lanczos RGBA enlargement with exact nearest source alpha',
        'frames': list(range(21)), 'output_size': [2560, 1440],
        'captures': [str(baseline), str(qwen), str(normal)],
        'runtime_restored': True, 'status': 'captured-pending-visual-verdict',
    }
    (out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
