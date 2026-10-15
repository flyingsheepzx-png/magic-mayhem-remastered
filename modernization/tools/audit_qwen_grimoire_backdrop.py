"""Baseline-first, three-way game capture of the Grimoire backdrop."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import time

from PIL import Image, ImageChops, ImageStat

from compare_hd_baseline import CaptureSession, baseline_identity, sha
from wide169_build import ROOT


REL = 'Interface/Grimoire/800x600/Backdrop.JPG'
PACKAGE = ROOT / 'modernization/playtests/mixed-ui-v4'
EXPECTED = '09c3fff8e320076374aaeb465c30461b80c893748a172952367d046dd27c68c1'


def framed_jpeg(image):
    canvas = Image.new('RGB', (2560, 1440))
    canvas.paste(image.convert('RGB'), (320, 0))
    buffer = io.BytesIO()
    canvas.save(buffer, 'JPEG', quality=100, subsampling=0)
    return buffer.getvalue()


def capture(label, out, suffix):
    with CaptureSession(label, out, 'mixed-ui-v4') as session:
        session.shot('menu-' + suffix)
        session.click_base(640, 396)
        time.sleep(1)
        session.shot('realm-' + suffix)
        session.require_visible('realm-' + suffix)
        session.click_base(976, 66)
        time.sleep(1)
        session.shot('grimoire-' + suffix)
        session.require_visible('grimoire-' + suffix)
        session.click_base(989, 650)
        time.sleep(.8)
        session.shot('grimoire-next-' + suffix)
        session.require_visible('grimoire-next-' + suffix)
    result = json.loads((out / label / 'capture.json').read_text(encoding='utf-8'))
    if not result.get('restored') or result.get('error'):
        raise RuntimeError('Game session was not restored: ' + suffix)
    return out / label / f'grimoire-{suffix}-2560x1440.png'


def main():
    baseline_identity()
    manifest_path = PACKAGE / 'manifest.json'
    asset_path = PACKAGE / 'game-wide169' / REL
    original_asset = asset_path.read_bytes()
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    key = 'game-wide169/' + REL
    if sha(asset_path) != EXPECTED or manifest['files'].get(key) != EXPECTED:
        raise RuntimeError('Unknown Grimoire backdrop candidate')
    if any(sha(PACKAGE / name) != digest for name, digest in manifest['files'].items()):
        raise RuntimeError('Candidate manifest mismatch')
    queue = json.loads((ROOT / 'modernization/assets/hd/hd-queue.json').read_text(encoding='utf-8'))
    row = next(record for record in queue['records'] if record['source'] == REL)
    source = ROOT / 'modernization/assets/hd/source-original' / REL
    qwen = ROOT / 'modernization/assets/hd/pack/Interface/Grimoire/800x600/Backdrop.png'
    if row['status'] != 'done' or sha(source) != row['source_sha256'] or sha(qwen) != row['output_sha256']:
        raise RuntimeError('Source or Qwen output identity mismatch')
    with Image.open(source) as s, Image.open(qwen) as q:
        if s.size != (800, 600) or q.size != (1920, 1440):
            raise RuntimeError('Wrong source or Qwen geometry')
        qwen_bytes = framed_jpeg(q)
        plain_bytes = framed_jpeg(s.resize((1920, 1440), Image.Resampling.LANCZOS))
    if qwen_bytes != original_asset:
        raise RuntimeError('Candidate is not verified Qwen output')

    out = ROOT / 'modernization/assets/hd/qwen-value-audits' / str(time.time_ns())
    out.mkdir(parents=True)
    for name in ('baseline-run', 'qwen-run', 'plain-run'):
        (out / name).mkdir()
    (out / 'rollback-backdrop.JPG').write_bytes(original_asset)
    (out / 'rollback-manifest.json').write_bytes(original_manifest)
    try:
        baseline = capture('baseline', out / 'baseline-run', 'baseline')
        qwen_capture = capture('hd', out / 'qwen-run', 'qwen')
        asset_path.write_bytes(plain_bytes)
        manifest['files'][key] = hashlib.sha256(plain_bytes).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        plain_capture = capture('hd', out / 'plain-run', 'plain')
    finally:
        asset_path.write_bytes(original_asset)
        manifest_path.write_bytes(original_manifest)
    if asset_path.read_bytes() != original_asset or manifest_path.read_bytes() != original_manifest:
        raise RuntimeError('Candidate rollback failed')
    if any(sha(PACKAGE / name) != digest for name, digest in
           json.loads(original_manifest)['files'].items()):
        raise RuntimeError('Candidate package changed after rollback')
    with Image.open(baseline) as b, Image.open(qwen_capture) as q, Image.open(plain_capture) as p:
        images = [b.convert('RGB'), q.convert('RGB'), p.convert('RGB')]
        triple = Image.new('RGB', (7680, 1440))
        for index, image in enumerate(images):
            triple.paste(image, (2560 * index, 0))
        triple.save(out / 'grimoire-baseline-qwen-plain-7680x1440.png')
        difference = ImageChops.difference(images[1], images[2])
        mean_difference = round(sum(ImageStat.Stat(difference).mean) / 3, 3)
    report = {
        'source': REL,
        'source_sha256': row['source_sha256'],
        'qwen_png_sha256': row['output_sha256'],
        'qwen_runtime_sha256': EXPECTED,
        'plain_runtime_sha256': hashlib.sha256(plain_bytes).hexdigest(),
        'output_size': [2560, 1440],
        'game_captures': {'baseline': str(baseline), 'qwen': str(qwen_capture), 'plain': str(plain_capture)},
        'mean_abs_rgb_difference': mean_difference,
        'runtime_restored': True,
        'status': 'captured-pending-visual-verdict',
    }
    (out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
