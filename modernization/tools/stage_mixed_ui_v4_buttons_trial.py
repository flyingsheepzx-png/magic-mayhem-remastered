"""Reversible Buttons.spr size trial in isolated v4 only."""
from pathlib import Path
import json

from compare_hd_baseline import baseline_identity
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB, build, sha


REL = 'Sprites/Buttons.spr'


def stage():
    baseline_identity()
    backup = BASE / 'before-buttons-trial'
    if backup.exists():
        raise RuntimeError('Buttons trial backup already exists')
    temp = BASE / 'sprite-derivatives-buttons'
    temp.mkdir(exist_ok=True)
    row = build(REL, temp)
    saved = backup / REL
    saved.parent.mkdir(parents=True)
    saved.write_bytes((LAB / REL).read_bytes())
    (LAB / REL).write_bytes((temp / REL).read_bytes())
    report = dict(status='trial-requires-page-and-battle-comparison', file=row)
    (BASE / 'buttons-trial-stage.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest_path = BASE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['game-wide169/' + REL] = row['sha256']
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    stage()
