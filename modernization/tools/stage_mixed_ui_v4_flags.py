"""Stage hash-verified Qwen realm flags only in isolated v4."""
import json
from compare_hd_baseline import baseline_identity
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB, build

REL='Interface/RealmViewer/Generic/flags.spr'

def stage():
    baseline_identity()
    backup=BASE/'before-realm-flags'
    if backup.exists():raise RuntimeError('Realm flag backup already exists')
    temp=BASE/'sprite-derivatives-flags';temp.mkdir(exist_ok=True)
    row=build(REL,temp)
    saved=backup/REL;saved.parent.mkdir(parents=True)
    saved.write_bytes((LAB/REL).read_bytes())
    (LAB/REL).write_bytes((temp/REL).read_bytes())
    report=dict(status='staged-requires-paired-game-verification',file=row)
    (BASE/'realm-flags-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    path=BASE/'manifest.json';manifest=json.loads(path.read_text())
    manifest['files']['game-wide169/'+REL]=row['sha256']
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':stage()
