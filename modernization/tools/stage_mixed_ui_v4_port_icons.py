"""Build a page-specific six-frame Qwen variant of v4 SplIcons."""
from pathlib import Path
import json
import struct
from PIL import Image, ImageChops
from spr_assets import read_spr, decode
from stage_mixed_ui_v3_sprites import encode
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB, PACK, sha

REL = 'Sprites/SplIcons.spr'
TARGETS = {43, 54, 73, 99, 100, 107}
EXPECTED = 'ea65414ca05b282c5b7fba3c05be469183d0406797b34d9c2cfb64231ff12fa8'
SOURCE = 'c4c47ba065669878afdc197558e3ad8a71d86bf4e0cfceda2f7d016e41b50e29'

def stage():
    path = LAB / REL
    raw = path.read_bytes()
    if sha(raw) != EXPECTED:
        raise RuntimeError('Unknown v4 SplIcons source')
    manifest_path = BASE / 'manifest.json'
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest['files']['game-wide169/' + REL] != EXPECTED:
        raise RuntimeError('Manifest source mismatch')
    palettes, frames = read_spr(path)
    if palettes or len(frames) != 234:
        raise RuntimeError('Unexpected frame container')
    meta_raw = (PACK / REL / 'sprite.json').read_bytes()
    meta = json.loads(meta_raw)
    if not meta['complete'] or meta['scale'] != 2 or meta['source_sha256'] != SOURCE:
        raise RuntimeError('Unknown Qwen source')
    records = {row['index']: row for row in meta['frames']}
    origin = [min(f['offset'][axis] for f in frames if f['width']) for axis in range(2)]
    encoded = []
    for frame in frames:
        i = frame['index']
        if i not in TARGETS:
            encoded.append(frame['data'])
            continue
        row = records[i]
        png = PACK / REL / row['file']
        if (sha(png.read_bytes()) != row['sha256'] or
                row['source_size'] != [frame['width'], frame['height']] or
                row['offset'] != frame['offset'] or row['flags'] != list(frame['flags'])):
            raise RuntimeError('Qwen frame mismatch: ' + str(i))
        with Image.open(png) as opened:
            if list(opened.size) != meta['target_frame_size']:
                raise RuntimeError('Qwen canvas mismatch')
            x, y = [2 * (frame['offset'][axis] - origin[axis]) for axis in range(2)]
            image = opened.convert('RGBA').crop((x, y,
                x + frame['width'] * 2, y + frame['height'] * 2))
        expected_alpha = decode(palettes, frame).getchannel('A').resize(
            image.size, Image.Resampling.NEAREST)
        image.putalpha(expected_alpha)
        encoded.append(encode(frame, image))
    output = bytearray(raw[:24])
    position = 0
    for data in encoded:
        output.extend(struct.pack('<I', position))
        position += len(data)
    for data in encoded:
        output.extend(data)
    struct.pack_into('<I', output, 4, len(output))
    temp = BASE / 'sprite-derivatives-port-icons' / REL
    temp.parent.mkdir(parents=True, exist_ok=True)
    temp.write_bytes(output)
    new_palettes, new_frames = read_spr(temp)
    if new_palettes or len(new_frames) != 234:
        raise RuntimeError('SPR roundtrip failed')
    for before, after in zip(frames, new_frames):
        if before['index'] not in TARGETS:
            if before['data'] != after['data']:
                raise RuntimeError('Untargeted frame changed')
        else:
            if (after['offset'] != [v * 2 for v in before['offset']] or
                    after['name'] != before['name'] or
                    [after['width'], after['height']] !=
                        [before['width'] * 2, before['height'] * 2]):
                raise RuntimeError('Target frame metadata mismatch')
            alpha = decode(palettes, before).getchannel('A').resize(
                (after['width'], after['height']), Image.Resampling.NEAREST)
            if ImageChops.difference(alpha,
                    decode(new_palettes, after).getchannel('A')).getbbox():
                raise RuntimeError('Target alpha mismatch')
    target = LAB / 'Sprites/port-icons.spr'
    old_target = target.read_bytes() if target.exists() else None
    try:
        target.write_bytes(output)
        digest = sha(output)
        manifest['files']['game-wide169/Sprites/port-icons.spr'] = digest
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    except Exception:
        if old_target is None:
            target.unlink(missing_ok=True)
        else:
            target.write_bytes(old_target)
        manifest_path.write_bytes(manifest_raw)
        raise
    report = {'status': 'page-specific-variant-staged',
              'source_sha256': EXPECTED, 'sha256': digest,
              'variant_path': 'Sprites/port-icons.spr',
              'frames_enlarged': sorted(TARGETS),
              'frames_preserved': len(frames) - len(TARGETS),
              'qwen_manifest_sha256': sha(meta_raw)}
    (BASE / 'port-icons-stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    stage()
