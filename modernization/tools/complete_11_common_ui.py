"""Resumable authenticated SeedVR common UI background derivatives and rollback."""
import argparse,base64,json,shutil,time,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import build_remastered_11 as b
import seedvr_ui_11 as s
from build_11_campaign_ui import api,guard,replace
from install_11_minimap_v2 import idle
OUT=b.ROOT/'modernization/assets/hd/seedvr2-common-ui-1.1'
PLAN=OUT/'plan.json';BACK=b.ROOT/'modernization/backups/remastered-1.1-common-ui'
RT=b.TARGET/'runtime';MANIFEST=b.TARGET/'manifest.json'
NAMES=['dlgback 800x600','dlgback 640x480','Scroll','smallScroll','border800x600-1','border800x600-2','border640x480-1','border640x480-2']
def preserve_keys(image,old):
 result=guard(image,old);a=np.array(result);original=np.array(old)
 # Scroll uses native yellow RGB565 key in addition to blue/magenta families.
 yellow=np.all(original==[255,255,0],axis=2);extra=np.all(a==[255,255,0],axis=2)&~yellow
 a[yellow]=original[yellow];a[extra]=original[extra]
 return Image.fromarray(a)
def prepare():
 b.verify();OUT.mkdir(parents=True,exist_ok=True)
 if PLAN.exists():return
 records=[]
 for name in NAMES:
  rel='Bitmaps/'+name+'.PNG';source=next(p for p in (s.ORIG/'Bitmaps').iterdir() if p.stem.lower()==name.lower() and p.suffix.lower()=='.bmp')
  im=Image.open(source).convert('RGB');target=RT/rel;assert im.size==Image.open(target).size
  array=np.array(im);array[s.keys(im)]=[128,104,72];inp=OUT/'inputs'/(name+'.PNG');inp.parent.mkdir(exist_ok=True);Image.fromarray(array).save(inp)
  width,height=im.size;scale=max(2,512/min(width,height));size=[round(width*scale),round(height*scale)]
  records.append(dict(path=rel,source=str(source),source_sha256=b.sha(source),before_sha256=b.sha(target),input=str(inp),input_sha256=b.sha(inp),native_size=list(im.size),request_size=size,status='pending'))
 b.write(PLAN,dict(model=s.MODEL,records=records,policy='original dimensions for shared battle resources; separate2xUI confirmation sibling',manifest_before_sha256=b.sha(MANIFEST)))
def generate():
 prepare();p=json.loads(PLAN.read_text());assert api('/api/status')['mode']=='managed'
 for r in p['records']:
  if 'job_id' in r:continue
  inp=Path(r['input']);assert b.sha(inp)==r['input_sha256']
  key='mm11-common-ui-'+r['input_sha256'][:24];result=api('/workbench/api/upscale/image',dict(data_url='data:image/png;base64,'+base64.b64encode(inp.read_bytes()).decode(),model=s.MODEL,width=r['request_size'][0],height=r['request_size'][1],scale=2),key)
  r.update(job_id=result['job_id'],status='submitted');b.write(PLAN,p);print('Queued',r['path'],r['job_id'],flush=True)
 for r in p['records']:
  if r['status']=='complete':continue
  deadline=time.monotonic()+1800
  while True:
   job=api('/api/jobs/'+r['job_id'])
   if job['state']=='succeeded':
    raw=Path(job['result']['file']).resolve();assert raw.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve())
    saved=OUT/'model-results'/Path(r['path']).name;saved.parent.mkdir(exist_ok=True);shutil.copy2(raw,saved)
    source=Path(r['source']);assert b.sha(source)==r['source_sha256'];old=Image.open(source).convert('RGB')
    im=Image.open(saved).convert('RGB');native=preserve_keys(im.resize(tuple(r['native_size']),Image.Resampling.LANCZOS),old)
    output=OUT/'runtime'/r['path'];output.parent.mkdir(parents=True,exist_ok=True);native.save(output)
    r.update(output=str(output),sha256=b.sha(output),model_output=str(saved),model_output_sha256=b.sha(saved),status='complete',colour_keys_exact=True)
    if r['path']=='Bitmaps/dlgback 800x600.PNG':
     rel='Bitmaps/hd-ui/dlgback 800x600.PNG';hd=OUT/'runtime'/rel;hd.parent.mkdir(parents=True,exist_ok=True)
     size=(832,560);guard(im.resize(size,Image.Resampling.LANCZOS),old.resize(size,Image.Resampling.NEAREST)).save(hd)
     r['hd_variant']=dict(path=rel,output=str(hd),sha256=b.sha(hd),before_sha256=b.sha(RT/rel),size=list(size))
    b.write(PLAN,p);print('Completed',r['path'],flush=True);break
   if job['state'] in ['failed','cancelled','recovery_required']:raise RuntimeError(str(job.get('error') or job['state']))
   if time.monotonic()>deadline:raise TimeoutError('Resume owned job '+r['job_id'])
   time.sleep(3)
def install():
 idle();b.verify();p=json.loads(PLAN.read_text());assert all(r['status']=='complete' for r in p['records'])
 m=json.loads(MANIFEST.read_text(encoding='utf-8'));updates={}
 for r in p['records']:
  for item in [r]+([r['hd_variant']] if 'hd_variant' in r else []):
   target=RT/item['path'];out=Path(item['output']);assert b.sha(target)==item['before_sha256'] and b.sha(out)==item['sha256']
   updates[target]=out.read_bytes();m['files'][item['path']]=item['sha256']
 m['common_ui_seedvr']=dict(model=p['model'],plan=str(PLAN),backgrounds=8,ui_variants=1,geometry_unchanged=True,acceptance='asset checks passed; user visual acceptance pending')
 updates[MANIFEST]=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode();BACK.mkdir(exist_ok=False)
 before={path:path.read_bytes() for path in updates};rows=[]
 for path,raw in before.items():
  rel=path.relative_to(b.ROOT).as_posix();out=BACK/'project'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);rows.append(dict(path=rel,sha256=hashlib.sha256(updates[path]).hexdigest()))
 b.write(BACK/'installation.json',dict(files=rows))
 try:
  for path,raw in updates.items():replace(path,raw)
  b.verify()
 except BaseException:
  for path,raw in before.items():replace(path,raw)
  raise
 print('Installed8 backgrounds and1HDmodal variant; user testing pending')
def rollback():
 idle();p=json.loads((BACK/'installation.json').read_text())
 for r in p['files']:assert b.sha(b.ROOT/r['path'])==r['sha256']
 for r in p['files']:replace(b.ROOT/r['path'],(BACK/'project'/r['path']).read_bytes())
 b.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','generate','install','rollback']);globals()[p.parse_args().action]()
