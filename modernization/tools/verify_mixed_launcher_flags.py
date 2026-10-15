"""Verify direct isolated launcher and optional sharpen with same save."""
import json
import os
from pathlib import Path
import sys
import time

from PIL import Image

from compare_hd_baseline import CaptureSession, ROOT, sha


def main():
    runtime = ROOT / 'modernization/playtests/mixed-ui-v4/game-wide169'
    fixture = runtime / 'Save/test2.sav'
    source = ROOT / 'modernization/backups/save-recovery/1790661735830701800/test2.sav'
    expected = '56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d'
    if fixture.exists() or sha(source) != expected:
        raise RuntimeError('Fixture gate failed')
    out = ROOT / 'modernization/assets/hd/launcher-mixed-fix' / str(time.time_ns())
    out.mkdir(parents=True)
    names = ('MM_PROBE_MIXED_RENDER', 'MM_PROBE_MIXED_FONTS', 'MM_PROBE_BATTLE_SHARPEN')
    previous = {name: os.environ.get(name) for name in names}
    results = []
    try:
        fixture.write_bytes(source.read_bytes())
        os.environ.pop(names[0], None)
        os.environ.pop(names[1], None)
        for level in ('0', '1'):
            os.environ[names[2]] = level
            run = out / f'level-{level}'
            run.mkdir()
            with CaptureSession('hd', run, 'mixed-ui-v4', launcher_sets_mixed=True) as session:
                session.shot('menu')
                session.load_fixture('test2', False)
                session.shot('battle')
                with Image.open(session.records['battle']['native']) as image:
                    region = image.convert('RGB').crop((1700, 200, 2400, 1000))
                    lit = sum(max(pixel) > 8 for pixel in region.get_flattened_data()) / (region.width * region.height)
                if lit < .2:
                    raise RuntimeError(f'Battle right side black: {lit}')
                session.key(0x1b)
                time.sleep(.4)
                session.shot('escape')
                if [460, 276, 820, 324] not in [c['rect'] for c in session.controls()]:
                    raise RuntimeError('Esc interaction failed')
                row = {'level': level, 'right_side_lit_fraction': lit,
                       'menu': session.records['menu']['native'],
                       'battle': session.records['battle']['native'],
                       'escape': session.records['escape']['native']}
                results.append(row)
                print(row, flush=True)
        (out / 'launcher-check.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
        print(out, flush=True)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        if fixture.exists() and sha(fixture) == expected:
            fixture.unlink()


if __name__ == '__main__':
    main()
