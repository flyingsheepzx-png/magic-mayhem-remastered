"""Read-only verification of saved production media and installed UI geometry.

Can audit installed batches while Manager jobs continue; never edits runtime.
Final mode requires every planned asset/job to have completed.
"""
from pathlib import Path
import argparse, json, time
import numpy as np
from PIL import Image
import seedvr_ui_11 as s

def load_plan():
 for attempt in range(20):
  try:return json.loads(s.PLAN.read_text(encoding='utf-8'))
  except json.JSONDecodeError:
   if attempt==19:raise
   time.sleep(.1)

def audit(final=False):
 plan=load_plan(); rows=[]; failures=[]
 for a in plan['assets']:
  if a['status']!='installed':continue
  try:
   output=Path(a['output']);runtime=s.RT/a['path'];old=s.BACK/'runtime'/a['path']
   assert s.sha(output)==s.sha(runtime)==a['sha256'], 'Output/runtime hash mismatch'
   assert s.sha(old)==a['before_sha256'], 'Rollback hash mismatch'
   assert s.sha(Path(a['source']))==a['source_sha256'], 'Original hash mismatch'
   if a.get('approved_source'):
    assert s.sha(Path(a['approved_source']))==a['approved_source_sha256']==a['sha256'], 'Approved map source changed'
   row=dict(path=a['path'],sha256=a['sha256'])
   if a['type']=='raster':
    with Image.open(output) as image:
     fmt=image.format;image.load();actual=image.convert('RGB')
    with Image.open(old) as image:before=image.convert('RGB')
    geometry_scale=a.get('geometry_scale',1)
    if geometry_scale!=1:before=before.resize((before.width*geometry_scale,before.height*geometry_scale),Image.Resampling.NEAREST)
    assert actual.size==before.size==tuple(a['size']), 'Raster geometry changed'
    expected=a.get('runtime_format','PNG')
    assert fmt==expected, 'Wrong encoded codec'
    assert np.array_equal(s.keys(actual),s.keys(before)), 'Saved colour-key coverage changed'
    row.update(size=list(actual.size),codec=fmt,key_pixels=int(s.keys(actual).sum()))
    if a['canvas']:
     pixels=np.array(actual)
     assert not pixels[:,:320].any() and not pixels[:,2240:].any(), 'Native UI margins changed'
    if expected=='JPEG':
     master=output.with_suffix('.PNG')
     with Image.open(master) as image:
      assert image.format=='PNG' and image.size==actual.size, 'Missing lossless JPEG master'
     row['png_master_sha256']=s.sha(master)
   else:
    bp,bf=s.read_spr(old);ap,af=s.read_spr(output)
    assert len(bf)==len(af)==a['frames'], 'Sprite frame count changed'
    opaque=0
    for b,n in zip(bf,af):
     geometry_scale=a.get('geometry_scale',1)
     assert n['name']==b['name'] and n['offset']==[v*geometry_scale for v in b['offset']] and all(n[k]==b[k]*geometry_scale for k in ('width','height')), 'Frame geometry changed'
     baseline_alpha=s.decode(bp,b).getchannel('A')
     if geometry_scale!=1:baseline_alpha=baseline_alpha.resize((n['width'],n['height']),Image.Resampling.NEAREST)
     ba=np.array(baseline_alpha);na=np.array(s.decode(ap,n).getchannel('A'))
     assert np.array_equal(ba,na), 'Frame alpha changed'
     opaque+=int((na>0).sum())
    row.update(frames=len(af),opaque_pixels=opaque,alpha_exact=True)
   rows.append(row)
  except (AssertionError,ValueError,OSError) as exc:
   failures.append(dict(path=a['path'],error=str(exc)))
 complete=all(a['status']=='installed' for a in plan['assets']) and all(t['status']=='complete' for t in plan['tasks'])
 if final and not complete:failures.append(dict(error='Final audit requires all planned jobs/assets complete'))
 result=dict(status='passed' if not failures else 'failed',final=final,complete=complete,
             planned_assets=len(plan['assets']),audited_assets=len(rows),assets=rows,failures=failures,
             scope='Saved media codecs, exact dimensions, alpha, keys, margins, original/rollback/runtime hashes; visual acceptance is separate')
 s.save(s.OUT/('audit-final.json' if final else 'audit-batch.json'),result)
 print(json.dumps({k:v for k,v in result.items() if k not in ('assets',)},indent=2))
 if failures:raise RuntimeError('Saved production audit failed')
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');audit(p.parse_args().final)
