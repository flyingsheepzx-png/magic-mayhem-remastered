"""Restore the user's preferred pre-SeedVR2 maps only, keeping other UI art."""
import json
from pathlib import Path
import seedvr_ui_11 as s

def restore():
 s.idle()
 plan=json.loads(s.PLAN.read_text(encoding='utf-8'))
 rows=[a for a in plan['assets'] if 'Interface/RealmViewer/800x600/' in a['path'] and a['path'].endswith('_Map.PNG')]
 assert len(rows)==3
 manifest=s.b.TARGET/'manifest.json';oldmanifest=manifest.read_bytes();m=json.loads(oldmanifest)
 backup=s.ROOT/'modernization/backups/remastered-1.1-qwen-map-restore'
 backup.mkdir(exist_ok=False);(backup/'manifest.json').write_bytes(oldmanifest)
 previous={}
 for a in rows:
  target=s.RT/a['path'];output=Path(a['output']);original=s.BACK/'runtime'/a['path']
  assert s.sha(target)==s.sha(output)==a['sha256'] and s.sha(original)==a['before_sha256']
  previous[target]=target.read_bytes()
  saved=backup/'runtime'/a['path'];saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(target.read_bytes())
  rejected=s.OUT/'rejected-seedvr-maps'/Path(a['path']).name
  rejected.parent.mkdir(exist_ok=True);rejected.write_bytes(output.read_bytes())
  approved=s.OUT/'approved-qwen-maps'/Path(a['path']).name
  approved.parent.mkdir(exist_ok=True);approved.write_bytes(original.read_bytes())
  a.update(artwork_model='Qwen Image / prior FullReadable',selection='User correction: prefer previous Qwen maps',
           superseded_seedvr_sha256=a['sha256'],approved_source=str(approved),approved_source_sha256=s.sha(approved))
 try:
  for a in rows:
   raw=Path(a['approved_source']).read_bytes();s.replace(Path(a['output']),raw);s.replace(s.RT/a['path'],raw)
   a['sha256']=s.sha(Path(a['output']));m['files'][a['path']]=a['sha256']
  plan['artwork_exceptions']=[a['path'] for a in rows]
  m['seedvr_ui']['artwork_exceptions']=dict(model='prior Qwen / FullReadable',paths=plan['artwork_exceptions'])
  s.replace(manifest,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
  s.save(s.PLAN,plan)
 except BaseException:
  for p,raw in previous.items():s.replace(p,raw)
  s.replace(manifest,oldmanifest);raise
 for a in rows:assert s.sha(s.RT/a['path'])==a['before_sha256']
 s.b.verify();print('Restored three previous Qwen maps; retained approved copies and SeedVR2 rollback')

if __name__=='__main__':restore()
