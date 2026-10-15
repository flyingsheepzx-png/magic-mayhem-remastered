"""Owned baseline-first captures for mixed battle cursor and load transition."""
from __future__ import annotations

import json
import time
from pathlib import Path
from PIL import Image, ImageChops
from compare_hd_baseline import CaptureSession, ROOT


def run(label: str, out: Path) -> dict:
    with CaptureSession(label, out, 'mixed-ui-v4', launcher_sets_mixed=True) as s:
        time.sleep(12 if label == 'baseline' else 1)
        s.shot('menu')
        s.load_fixture('test4', False)
        s.shot('battle-left')
        positions = [(500, 350), (1700, 350), (1700, 1050), (2500, 700)]
        records = []
        for n, (x, y) in enumerate(positions):
            s.message(0x200, x if s.hd else x // 2, y if s.hd else y // 2)
            time.sleep(.3)
            s.shot(f'cursor-{n}', move_cursor=False)
            records.append({'xy': [x, y], 'path': s.records[f'cursor-{n}']['output']})
        result = {'screens': records, 'engine_sha256': s.result['engine_sha256']}
    result['restored'] = s.result['restored']
    return result


def main():
    out = ROOT / 'modernization/assets/hd/cursor-loading-probe' / str(time.time_ns())
    out.mkdir(parents=True)
    result = {}
    for label in ('baseline', 'hd'):
        result[label] = run(label, out)
    for label in result:
        paths = [Path(p['path']) for p in result[label]['screens']]
        for i in range(1, len(paths)):
            with Image.open(paths[0]) as a, Image.open(paths[i]) as b:
                box = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox()
            result[label]['screens'][i]['difference_bbox'] = box
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__': main()
