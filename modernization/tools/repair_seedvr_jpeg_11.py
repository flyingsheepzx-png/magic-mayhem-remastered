"""Repair only decoded JPEG key mismatches before continuing production."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
import seedvr_ui_11 as s

def repair():
 s.idle();plan=json.loads(s.PLAN.read_text(encoding='utf-8'))
 mpath=s.b.TARGET/'manifest.json';m=json.loads(mpath.read_text(encoding='utf-8'));changed=[]
 for a in plan['assets']:
  if a['status']!='installed' or a.get('runtime_format')!='JPEG':continue
  out=Path(a['output']);old=Image.open(s.BACK/'runtime'/a['path']).convert('RGB')
  new=Image.open(out).convert('RGB')
  if np.array_equal(s.keys(old),s.keys(new)):continue
  rt=s.RT/a['path'];assert s.sha(out)==s.sha(rt)==a['sha256']
  backup=s.ROOT/'modernization/backups/remastered-1.1-jpeg-key-guard'/a['path']
  backup.parent.mkdir(parents=True,exist_ok=True)
  if backup.exists():raise RuntimeError('Existing JPEG repair backup')
  backup.write_bytes(rt.read_bytes());backup.with_suffix('.PNG').write_bytes(out.with_suffix('.PNG').read_bytes())
  master=Image.open(out.with_suffix('.PNG')).convert('RGB')
  a['jpeg_guard_iterations']=s.save_jpeg_verified(master,out,old)
  s.replace(rt,out.read_bytes());a['sha256']=s.sha(out);m['files'][a['path']]=a['sha256'];changed.append(a['path'])
 s.replace(mpath,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));s.save(s.PLAN,plan)
 print('Repaired JPEG decoded key coverage:',changed);s.b.verify()

if __name__=='__main__':repair()
