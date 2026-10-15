"""Stage verified Qwen options controls in v4 for paired native testing."""
from pathlib import Path
import json

from compare_hd_baseline import baseline_identity
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB, build, sha


SOURCES = ('Sprites/radiobuttons.spr', 'Sprites/slider.spr')


def stage():
    baseline_identity()
    backup = BASE / 'before-options-sprites'
    if backup.exists():
        raise RuntimeError('Options sprite backup already exists')
    temp = BASE / 'sprite-derivatives-options'
    temp.mkdir(exist_ok=True)
    rows = [build(rel, temp) for rel in SOURCES]
    backup.mkdir()
    for row in rows:
        rel = row['path']
        saved = backup / rel
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes((LAB / rel).read_bytes())
        (LAB / rel).write_bytes((temp / rel).read_bytes())
    report = dict(status='staged-requires-paired-game-verification', files=rows)
    (BASE / 'options-sprites-stage.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest_path = BASE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for row in rows:
        manifest['files']['game-wide169/' + row['path']] = row['sha256']
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    stage()
