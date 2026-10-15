"""Resumable Manager-owned SeedVR2 UI production, transactional per-file install.

Never runs GPU inference directly. Old artwork supplies geometry/masks only;
model inputs always come from immutable originals/latest baseline corrections.
"""
from pathlib import Path
import argparse,base64,hashlib,json,os,struct,time,urllib.request
import numpy as np
from PIL import Image,ImageDraw
import build_remastered_11 as b
from spr_assets import read_spr,decode
from stage_mixed_ui_v3_sprites import encode
from install_11_realm_fix import idle,replace
ROOT=b.ROOT;RT=b.TARGET/'runtime';ORIG=ROOT/'modernization/assets/hd/source-original'
OUT=ROOT/'modernization/assets/hd/seedvr2-ui-1.1';PLAN=OUT/'plan.json'
BACK=ROOT/'modernization/backups/remastered-1.1-seedvr-ui'
MODEL='seedvr2_ema_7b_sharp_fp8_e4m3fn.safetensors'
BASE='http://127.0.0.1:8790'
def sha(p):return b.sha(p)
def save(p,j):p.parent.mkdir(parents=True,exist_ok=True);b.write(p,j)
def api(route,payload=None,key=None):
 headers={'Content-Type':'application/json'}
 if key:headers['Idempotency-Key']=key
 req=urllib.request.Request(BASE+route,data=None if payload is None else json.dumps(payload).encode(),headers=headers)
 with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def keys(im):
 a=np.array(im.convert('RGB'));blue=(a[:,:,2]>220)&(a[:,:,0]<35)&(a[:,:,1]<35);pink=(a[:,:,0]>220)&(a[:,:,2]>220)&(a[:,:,1]<35)
 return blue|pink
def save_jpeg_verified(im,destination,old):
 """Guard colour-key thresholds after lossy encoding, not only before it."""
 mask=keys(old);a=np.array(im);baseline=np.array(old)
 for attempt in range(12):
  Image.fromarray(a).save(destination,quality=100,subsampling=0)
  with Image.open(destination) as saved:actual=keys(saved)
  if np.array_equal(actual,mask):
   master=Image.fromarray(a);assert np.array_equal(keys(master),mask)
   master.save(destination.with_suffix('.PNG'));return attempt
  extra=actual&~mask;missing=mask&~actual
  # Move only affected opaque pixels away from JPEG threshold crossings.
  a[extra]=baseline[extra];a[:,:,1][extra]=np.maximum(a[:,:,1][extra],64)
  # Genuine key pixels get canonical RGB with ample threshold headroom.
  pink=missing&(baseline[:,:,0]>220)
  a[missing]=[0,0,255];a[pink]=[255,0,255]
 raise RuntimeError('JPEG colour-key coverage cannot be preserved: '+str(destination))
def prepare():
 if PLAN.exists():print('Existing immutable production plan');return
 b.verify();OUT.mkdir(parents=True,exist_ok=True);BACK.mkdir(exist_ok=False)
 (BACK/'manifest.json').write_bytes((b.TARGET/'manifest.json').read_bytes())
 assets=[];tasks=[];seen={};unsupported=[]
 # Select every independent UI raster at its currently adapted size, including
 # book pages. Existing640 variants derive from the same original model output.
 rasters=[p for p in RT.glob('Interface/**/*.PNG') if '640x480' not in p.parts]
 for p in sorted(rasters):
  rel=p.relative_to(RT).as_posix();stem=ORIG/rel;source=None
  for ext in ['.BMP','.JPG','.PNG']:
   q=stem.with_suffix(ext)
   if q.exists():source=q;break
  if source is None:raise RuntimeError('Missing original raster '+rel)
  with Image.open(source) as im:original=im.convert('RGB')
  current=Image.open(p).convert('RGB');size=current.size;canvas=(size==(2560,1440))
  target=(1920,1440) if canvas else size
  # Native bars have too few pixels for meaningful generative restoration.
  # They are reproduced from original with deterministic resizing.
  procedural=min(original.size)<24
  digest=sha(source);taskid='r-'+digest[:20]
  if not procedural and taskid not in seen:
   model_input=original.copy();a=np.array(model_input);a[keys(model_input)]=[128,104,72];model_input=Image.fromarray(a)
   inp=OUT/'inputs'/f'{taskid}.png';inp.parent.mkdir(exist_ok=True);model_input.save(inp)
   # Respect aspect ratio during inference; reshape only as required by the
   # existing native page layout and exact colour-key masks on output.
   short=max(64,min(target));long=max(short,round(max(original.size)/min(original.size)*short));long=min(4096,long)
   task=dict(id=taskid,input=str(inp),input_sha256=sha(inp),width=round(original.width/min(original.size)*short),height=round(original.height/min(original.size)*short),status='pending',kind='raster')
   tasks.append(task);seen[taskid]=task
  assets.append(dict(path=rel,type='raster',source=str(source),source_sha256=digest,before_sha256=sha(p),size=list(size),content_size=list(target),canvas=canvas,task=None if procedural else taskid,status='pending'))
 # All currently-supported UI sprite containers, retaining established sizes.
 paths=[p for p in RT.glob('Interface/**/*.spr') if '640x480' not in p.parts and '640-480' not in p.name]
 paths += [RT/'Sprites'/n for n in ['Buttons.spr','radiobuttons.spr','slider.spr','CheckBox.spr','scrollbar.spr','Scrollbutt.spr','selbut.spr'] if (RT/'Sprites'/n).exists()]
 paths += [RT/'Sprites/port-icons.spr']
 # Controls first gives useful installable checkpoints while backgrounds queue.
 raster_tasks=tasks;tasks=[]
 for p in paths:
  rel=p.relative_to(RT).as_posix();source=ORIG/rel
  if rel=='Sprites/port-icons.spr':source=ORIG/'Sprites/SplIcons.spr'
  if not source.exists():raise RuntimeError('Missing original SPR '+rel)
  try:sp,sf=read_spr(source);cp,cf=read_spr(p)
  except ValueError as e:unsupported.append(dict(path=rel,reason=str(e)));continue
  assert len(sf)==len(cf)
  # The current baseline's corrected clasp outline is newer than immutable
  # source-original. Use that correction for frames0/1 only.
  corrected=None
  if rel=='Interface/Grimoire/800x600/icons.spr':corrected=read_spr(b.BASE/'runtime'/rel)
  aid='s-'+hashlib.sha256(rel.encode()).hexdigest()[:16];cells=[];atlases=[]
  atlas=Image.new('RGB',(512,512),'#303038');x=y=16;rowh=0;number=0
  def flush():
   nonlocal atlas,x,y,rowh,number,cells
   if not cells:return
   taskid=aid+'-'+str(number);inp=OUT/'inputs'/f'{taskid}.png';atlas.save(inp)
   tasks.append(dict(id=taskid,input=str(inp),input_sha256=sha(inp),width=2048,height=2048,status='pending',kind='atlas'))
   atlases.append(dict(task=taskid,cells=cells));atlas=Image.new('RGB',(512,512),'#303038');x=y=16;rowh=0;number+=1;cells=[]
  for i,(s,c) in enumerate(zip(sf,cf)):
   if not s['width']:continue
   im=decode(sp,s)
   if corrected and i<2:im=decode(corrected[0],corrected[1][i])
   if x+im.width+16>512:x=16;y+=rowh+24;rowh=0
   if y+im.height+16>512:flush()
   if max(im.size)>480:raise RuntimeError('Unbounded sprite atlas '+rel)
   atlas.paste(im,(x,y),im);cells.append(dict(index=i,rect=[x,y,x+im.width,y+im.height]));x+=im.width+24;rowh=max(rowh,im.height)
  flush()
  assets.append(dict(path=rel,type='sprite',source=str(source),source_sha256=sha(source),before_sha256=sha(p),atlases=atlases,status='pending',frames=len(sf)))
 tasks+=raster_tasks
 # Save masks/geometry baseline per changed runtime file before any install.
 for asset in assets:
  p=BACK/'runtime'/asset['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((RT/asset['path']).read_bytes())
 save(PLAN,dict(model=MODEL,engine_sha256=sha(RT/'Chaos-Wide169-engine.exe'),initial_manifest_sha256=sha(b.TARGET/'manifest.json'),tasks=tasks,assets=assets,unsupported=unsupported,status='prepared',policy='UI1920x1440, battle1280x720 scaled2; only artwork changes'))
 print('Prepared',len(assets),'assets,',len(tasks),'managed jobs;',unsupported,flush=True)
def production(plan):
 for task in plan['tasks']:
  if task['status']=='complete':continue
  result=OUT/'model-results'/(task['id']+'.png')
  if 'job_id' not in task:
   inp=Path(task['input']);assert sha(inp)==task['input_sha256']
   payload={'data_url':'data:image/png;base64,'+base64.b64encode(inp.read_bytes()).decode(),'model':MODEL,'width':task['width'],'height':task['height']}
   j=api('/workbench/api/upscale/image',payload,'mm11-seedvr-production-'+task['id']);task.update(job_id=j['job_id'],status='submitted');save(PLAN,plan)
  deadline=time.monotonic()+1800;last=None
  while True:
   j=api('/api/jobs/'+task['job_id']);state=j['state']
   if state!=last:print(task['id'],state,task['job_id'],flush=True);last=state
   if state=='succeeded':
    source=Path(j['result']['file']).resolve();assert source.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve())
    result.parent.mkdir(exist_ok=True);result.write_bytes(source.read_bytes());Image.open(result).verify()
    task.update(status='complete',output=str(result),output_sha256=sha(result));save(PLAN,plan);break
   if state in ['failed','cancelled','recovery_required']:raise RuntimeError(str(j))
   if time.monotonic()>deadline:raise TimeoutError('Owned job still '+state+'; resume saved job, no duplicate')
   time.sleep(3)
  build_ready(plan)
  install_ready(plan)
  print('Progress',sum(t['status']=='complete' for t in plan['tasks']),'/',len(plan['tasks']),'jobs;',sum(a['status']=='installed' for a in plan['assets']),'/',len(plan['assets']),'assets installed',flush=True)
def extend_jpeg():
 plan=json.loads(PLAN.read_text(encoding='utf-8'));existing={a['path'] for a in plan['assets']};tasks={t['id']:t for t in plan['tasks']};added=[]
 for p in sorted(RT.glob('Interface/**/*.JPG')):
  if '640x480' in p.parts or p.with_suffix('.PNG').exists():continue
  rel=p.relative_to(RT).as_posix()
  if rel in existing:continue
  source=ORIG/rel
  if not source.exists():raise RuntimeError('Missing original JPEG '+rel)
  original=Image.open(source).convert('RGB');current=Image.open(p).convert('RGB');size=current.size;canvas=size==(2560,1440);target=(1920,1440) if canvas else size
  taskid='r-'+sha(source)[:20]
  if taskid not in tasks:
   a=np.array(original);a[keys(original)]=[128,104,72];inp=OUT/'inputs'/(taskid+'.png');Image.fromarray(a).save(inp)
   short=max(64,min(target));w=round(original.width/min(original.size)*short);h=round(original.height/min(original.size)*short)
   # Loading bars need a larger input canvas rather than an extreme1:16 DiT
   # aspect ratio. Preserve their established width/height on extraction.
   crop=None
   if max(w,h)>4096:
    padded=Image.new('RGB',(original.width,original.width),'#303038');y=(original.width-original.height)//2;padded.paste(original,(0,y));padded.save(inp);w=h=1440;crop=[0,y,original.width,y+original.height]
   task=dict(id=taskid,input=str(inp),input_sha256=sha(inp),width=w,height=h,status='pending',kind='raster')
   if crop:task.update(source_crop=crop,source_canvas=[original.width,original.width])
   tasks[taskid]=task;plan['tasks'].append(task)
  asset=dict(path=rel,type='raster',source=str(source),source_sha256=sha(source),before_sha256=sha(p),size=list(size),content_size=list(target),canvas=canvas,task=taskid,status='pending',runtime_format='JPEG')
  saved=BACK/'runtime'/rel;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(p.read_bytes());plan['assets'].append(asset);added.append(rel)
 save(PLAN,plan);print('Added JPEG compatibility UI assets',len(added),'total',len(plan['assets']),'tasks',len(plan['tasks']))
def build_ready(plan):
 taskmap={t['id']:t for t in plan['tasks']}
 for asset in plan['assets']:
  if asset['status']!='pending':continue
  ids=[a['task'] for a in asset['atlases']] if asset['type']=='sprite' else ([asset['task']] if asset['task'] else [])
  if any(taskmap[i]['status']!='complete' for i in ids):continue
  source=Path(asset['source']);assert sha(source)==asset['source_sha256'];current=BACK/'runtime'/asset['path'];assert sha(current)==asset['before_sha256']
  destination=OUT/'runtime'/asset['path'];destination.parent.mkdir(parents=True,exist_ok=True)
  if asset.get('derivative_override'):
   override=Path(asset['derivative_override']);assert sha(override)==asset['derivative_override_sha256']
   destination.write_bytes(override.read_bytes())
   if asset.get('runtime_format')=='JPEG':destination.with_suffix('.PNG').write_bytes(override.with_suffix('.PNG').read_bytes())
   asset.update(output=str(destination),sha256=sha(destination),status='ready');save(PLAN,plan);continue
  if asset['type']=='raster':
   im=Image.open(Path(taskmap[asset['task']]['output']) if asset['task'] else source).convert('RGB')
   task=taskmap.get(asset['task'],{})
   if task.get('source_crop'):
    scale=im.width/task['source_canvas'][0];im=im.crop(tuple(round(v*scale) for v in task['source_crop']))
   im=im.resize(tuple(asset['content_size']),Image.Resampling.LANCZOS)
   if asset['canvas']:
    canvas=Image.new('RGB',tuple(asset['size']));canvas.paste(im,(320,0));im=canvas
   elif asset.get('page_origin'):
    canvas=Image.new('RGB',tuple(asset['size']),(0,0,255));canvas.paste(im,tuple(asset['page_origin']));im=canvas
   old=Image.open(current).convert('RGB');mask=keys(old);a=np.array(im);old_a=np.array(old);a[mask]=old_a[mask]
   # Colour-key footprints must neither grow nor shrink after SR. Restore any
   # accidental key-coloured new pixel from the baseline at that coordinate.
   extra=keys(Image.fromarray(a))&~mask;a[extra]=old_a[extra];im=Image.fromarray(a)
   # Preserve lossless production PNG; native JPEG-only callers still require
   # their original suffix/codec. Do not disguise PNG bytes as JPEG.
   if asset.get('runtime_format')=='JPEG':
    asset['jpeg_guard_iterations']=save_jpeg_verified(im,destination,old)
   else:im.save(destination)
   assert im.size==old.size and np.array_equal(keys(im),mask)
   asset['verification']=dict(size_exact=True,colour_keys_exact=True,key_pixels=int(mask.sum()),format=asset.get('runtime_format','PNG'))
  else:
   sp,sf=read_spr(source);cp,cf=read_spr(current);images={}
   for atlas in asset['atlases']:
    task=taskmap[atlas['task']];p=Path(task['output']);assert sha(p)==task['output_sha256'];img=Image.open(p).convert('RGB');assert img.size==(2048,2048)
    for cell in atlas['cells']:
     i=cell['index'];c=cf[i];im=img.crop(tuple(v*4 for v in cell['rect'])).resize((c['width'],c['height']),Image.Resampling.LANCZOS).convert('RGBA');im.putalpha(decode(cp,c).getchannel('A'));images[i]=im
   payloads=[]
   for i,c in enumerate(cf):
    if i not in images:payloads.append(c['data']);continue
    block=bytearray(encode(c,images[i]));struct.pack_into('<2i',block,12,*c['offset']);payloads.append(bytes(block))
   raw=bytearray(current.read_bytes()[:24]);struct.pack_into('<II',raw,16,0,0);pos=0
   for block in payloads:raw.extend(struct.pack('<I',pos));pos+=len(block)
   for block in payloads:raw.extend(block)
   struct.pack_into('<I',raw,4,len(raw));destination.write_bytes(raw)
   p,frames=read_spr(destination);assert len(frames)==len(cf);maximum=0
   for i,(c,n) in enumerate(zip(cf,frames)):
    assert all(c[k]==n[k] for k in ['width','height','offset','name'])
    actual=np.array(decode(p,n));old=np.array(decode(cp,c));assert np.array_equal(actual[:,:,3],old[:,:,3])
    if i in images:
     wanted=np.array(images[i]);mask=wanted[:,:,3]>0
     if mask.any():maximum=max(maximum,int(np.abs(actual[:,:,:3].astype(int)-wanted[:,:,:3].astype(int))[mask].max()))
   assert maximum<=9
   asset['verification']=dict(frames=len(frames),metadata_exact=True,alpha_exact=True,maximum_rgb565_error=maximum)
  asset.update(status='built',output=str(destination),sha256=sha(destination));save(PLAN,plan)
def install_ready(plan):
 ready=[a for a in plan['assets'] if a['status']=='built']
 if not ready:return
 if (OUT/'test.lock').exists():print('Paired-test lock: installation held; GPU generation continues',flush=True);return
 try:idle()
 except RuntimeError:print('Game active: built files held for next safe checkpoint',flush=True);return
 manifest_path=b.TARGET/'manifest.json';m=json.loads(manifest_path.read_text(encoding='utf-8'))
 assert sha(RT/'Chaos-Wide169-engine.exe')==plan['engine_sha256']
 originals={RT/a['path']:(RT/a['path']).read_bytes() for a in ready};oldmanifest=manifest_path.read_bytes()
 for a in ready:assert sha(RT/a['path'])==a['before_sha256'] and sha(Path(a['output']))==a['sha256']
 try:
  for a in ready:replace(RT/a['path'],Path(a['output']).read_bytes());m['files'][a['path']]=a['sha256']
  m['seedvr_ui']=dict(model=MODEL,plan=str(PLAN),backup=str(BACK),installed=sum(a['status']=='installed' for a in plan['assets'])+len(ready),total=len(plan['assets']),runtime_acceptance='pending per-batch comparison/user testing')
  replace(manifest_path,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode())
  for a in ready:assert sha(RT/a['path'])==a['sha256'];a['status']='installed'
  save(PLAN,plan)
 except BaseException:
  for p,data in originals.items():replace(p,data)
  replace(manifest_path,oldmanifest);raise
 print('Installed batch',[a['path'] for a in ready],flush=True)
def run():
 plan=json.loads(PLAN.read_text(encoding='utf-8'));build_ready(plan);install_ready(plan);production(plan);build_ready(plan);install_ready(plan);b.verify()
 plan['status']='installed' if all(a['status']=='installed' for a in plan['assets']) else 'generated';save(PLAN,plan)
def rollback():
 idle();plan=json.loads(PLAN.read_text(encoding='utf-8'));m=json.loads((b.TARGET/'manifest.json').read_text(encoding='utf-8'))
 for a in plan['assets']:
  if a['status']!='installed':continue
  assert sha(RT/a['path'])==a['sha256'];src=BACK/'runtime'/a['path'];assert sha(src)==a['before_sha256'];replace(RT/a['path'],src.read_bytes());m['files'][a['path']]=a['before_sha256'];a['status']='built'
 m.pop('seedvr_ui',None);replace(b.TARGET/'manifest.json',(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());save(PLAN,plan);b.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','extend_jpeg','run','rollback']);globals()[p.parse_args().action]()
