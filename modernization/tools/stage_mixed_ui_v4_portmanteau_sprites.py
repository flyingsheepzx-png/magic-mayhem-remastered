"""Stage verified Qwen Portmanteau sprites in the isolated v4 runtime.

Keep the installed baseline and v3 playtest untouched. Decode every encoded
frame before replacing either file, and retain the exact source bytes for
rollback.
"""
from pathlib import Path
import hashlib
import json
import struct

from PIL import Image, ImageChops

from compare_hd_baseline import baseline_identity
from spr_assets import read_spr, decode
from stage_mixed_ui_v3_sprites import encode
from wide169_build import ROOT


BASE = ROOT / 'modernization/playtests/mixed-ui-v4'
LAB = BASE / 'game-wide169'
PACK = ROOT / 'modernization/assets/hd/pack'
SOURCES = (
    'Interface/SpellBox/800x600/mitems.spr',
    'Interface/SpellBox/800x600/Talisman.spr',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(rel, temp):
    source = LAB / rel
    raw = source.read_bytes()
    palettes, frames = read_spr(source)
    meta_path = PACK / rel / 'sprite.json'
    meta_raw = meta_path.read_bytes()
    meta = json.loads(meta_raw)
    if not meta['complete'] or meta['scale'] != 2 or sha(raw) != meta['source_sha256']:
        raise RuntimeError('Unknown or incomplete Qwen source: ' + rel)
    usable = [frame for frame in frames if frame['width'] and frame['height']]
    origin = [min(frame['offset'][axis] for frame in usable) for axis in range(2)]
    records = {record['index']: record for record in meta['frames']}
    if len(records) != len(frames):
        raise RuntimeError('Missing frame record: ' + rel)
    encoded = []
    wanted = []
    for frame in frames:
        if not frame['width']:
            image = Image.new('RGBA', (0, 0))
        else:
            row = records[frame['index']]
            png = PACK / rel / row['file']
            if (sha(png.read_bytes()) != row['sha256']
                    or row['source_size'] != [frame['width'], frame['height']]
                    or row['offset'] != frame['offset']
                    or row['flags'] != list(frame['flags'])):
                raise RuntimeError('Qwen frame identity mismatch: ' + str(png))
            with Image.open(png) as opened:
                if list(opened.size) != meta['target_frame_size']:
                    raise RuntimeError('Wrong Qwen sheet geometry: ' + str(png))
                x, y = [2 * (frame['offset'][axis] - origin[axis]) for axis in range(2)]
                image = opened.convert('RGBA').crop(
                    (x, y, x + frame['width'] * 2, y + frame['height'] * 2))
            mask = decode(palettes, frame).getchannel('A').resize(
                image.size, Image.Resampling.NEAREST)
            image.putalpha(mask)
        wanted.append(image)
        encoded.append(encode(frame, image))
    output = bytearray(raw[:24])
    struct.pack_into('<II', output, 16, 0, 0)
    offset = 0
    for frame in encoded:
        output.extend(struct.pack('<I', offset))
        offset += len(frame)
    for frame in encoded:
        output.extend(frame)
    struct.pack_into('<I', output, 4, len(output))
    dest = temp / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(output)
    new_palettes, new_frames = read_spr(dest)
    if new_palettes or len(new_frames) != len(frames):
        raise RuntimeError('SPR roundtrip frame count: ' + rel)
    maximum_error = 0
    for old, new, expected in zip(frames, new_frames, wanted):
        actual = decode(new_palettes, new)
        if (new['offset'] != [v * 2 for v in old['offset']]
                or new['flags'] != (0xffffffff, 0, 0)
                or new['name'] != old['name']):
            raise RuntimeError('SPR metadata mismatch: ' + rel)
        if ImageChops.difference(actual.getchannel('A'), expected.getchannel('A')).getbbox():
            raise RuntimeError('SPR alpha coverage mismatch: ' + rel)
        diff = ImageChops.difference(actual.convert('RGB'), expected.convert('RGB'))
        diff = Image.composite(diff, Image.new('RGB', diff.size), expected.getchannel('A'))
        maximum_error = max(maximum_error, max(channel[1] for channel in diff.getextrema()))
    if maximum_error > 9:
        raise RuntimeError('RGB565 quantization exceeded bound: ' + rel)
    return dict(path=rel, source_sha256=sha(raw), sha256=sha(output),
                frames=len(frames), maximum_rgb565_error=maximum_error,
                qwen_manifest_sha256=sha(meta_raw))


def stage():
    baseline_identity()
    backup = BASE / 'before-portmanteau-sprites'
    if backup.exists():
        raise RuntimeError('Portmanteau sprite backup already exists')
    temp = BASE / 'sprite-derivatives-portmanteau'
    temp.mkdir(exist_ok=True)
    rows = [build(rel, temp) for rel in SOURCES]
    backup.mkdir()
    for row in rows:
        rel = row['path']
        saved = backup / rel
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes((LAB / rel).read_bytes())
        (LAB / rel).write_bytes((temp / rel).read_bytes())
    report = dict(status='staged-requires-paired-game-verification',
                  coverage='exact original nearest 2x', files=rows)
    (BASE / 'portmanteau-sprites-stage.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest_path = BASE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for row in rows:
        manifest['files']['game-wide169/' + row['path']] = row['sha256']
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    stage()
