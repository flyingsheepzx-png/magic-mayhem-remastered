"""Bounded, resumable SeedVR2 SHEET review. All GPU inference via authenticated Manager FIFO.
Writes only this review directory. No gameplay, runtime edits, model downloads or cleanup.
python modernization/assets/creature-seedvr-sheet-expanded-20261001/run_expanded.py
"""
import os
from pathlib import Path
import sys,json,hashlib,base64,urllib.request,time,shutil,math,argparse
from PIL import Image
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'modernization/tools'))
from spr_assets import read_spr,decode
BASE='http://127.0.0.1:8790'
CRED=Path(os.environ['MM_LOCAL_MODEL_CREDENTIAL'])
MANIFEST=OUT/'manifest.json'
MODEL='seedvr2_ema_7b_sharp_fp8_e4m3fn.safetensors'
BG=(48,48,56)
SELECTION=[('Bat','bat',['AALF','ABLF'],'bat-retest'),('Dog','dog',['BALA','BCLA'],'ground-quadruped'),('skeleton','skeleton',['SBLA','SCLJ'],'humanoid-thin-limbs'),('Griffin','griffin',['GBLA','GCLJ'],'winged'),('Dragon','dragon',['DALA','DGLB'],'large-high-detail'),('Wraith','wraith',['WALA','WCLC'],'spectral-appearance'),('Phoenix','phoenix',['PALA','PBLD'],'bright-feather-effect-appearance')]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
def write(p,value):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def api(route,payload=None,key=None,comfy=False):
 headers={'Authorization':'Bearer '+json.loads(CRED.read_text())['token'],'Content-Type':'application/json'}
 if key:headers['Idempotency-Key']=key
 request=urllib.request.Request(('http://127.0.0.1:8791' if comfy else BASE)+route,headers=headers,data=None if payload is None else json.dumps(payload).encode())
 with urllib.request.urlopen(request,timeout=45) as r:return json.load(r)
def verify_sources(plan):
 for s in plan['sources']:
  for k in ['spr','ani']:
   assert sha(s[k])==s[k+'_sha256'],s[k]
   assert sha(s['copy_'+k])==s[k+'_sha256'],s['copy_'+k]
def native_frame(palettes,frame):
 selector=frame['variant']
 if palettes:
  assert 0<=selector<len(palettes),('invalid native palette selector',frame['name'],selector,len(palettes))
  frame={**frame,'palette':selector}
 else:assert selector==0xffffffff,('invalid RGB565 selector',frame['name'],selector)
 return frame
def audit_selectors(plan):
 audits=[]
 for source in plan['sources']:
  palettes,frames=read_spr(Path(source['spr']))
  for task in plan['jobs']:
   if task['creature']!=source['creature']:continue
   for row in task['frames']:
    frame=native_frame(palettes,frames[row['index']]);im=decode(palettes,frame)
    with Image.open(row['source_png']) as old:assert old.convert('RGBA').tobytes()==im.tobytes(),('previous input palette mismatch; refuse resume',task['name'],row['index'])
    row.update(palette_selector=frame['variant'],palette_count=len(palettes),pixel_format='palette8' if palettes else 'RGB565',mask_offset_32=frame['flags'][1],mask_offset_36=frame['flags'][2])
   audits.append({'job':task['name'],'palette_count':len(palettes),'selectors':sorted(set(r['palette_selector'] for r in task['frames']))})
 plan['palette_audit']=audits
 plan['field_semantics']={'flags[0] / variant / native +28':'palette selector; 0xffffffff for RGB565','flags[1] / native +32':'optional mask offset','flags[2] / native +36':'optional mask offset','palette_override':'legal native selector explicitly applied before decode; no reliance on reader default'}
 write(MANIFEST,plan)
def prepare():
 if MANIFEST.exists():return json.loads(MANIFEST.read_text())
 status=api('/api/status');assert status['mode']=='managed'
 catalog=api('/workbench/api/upscale/models');assert any(m['id']==MODEL and m['installed'] for m in catalog['models'])
 system=api('/system_stats',comfy=True)
 plan={'schema':1,'scope':'SeedVR2 SHEET only, isolated offline diagnostic, no ANI action/timing claims','created_at':time.time(),'model':MODEL,'background':BG,'policy':{'columns':4,'margin_native_px':32,'cell_min_side':128,'cell_round_multiple':32,'scale':2,'input_resampling':'none','unexpected_model_dimensions':'refuse; never squeeze','per_job_poll_bound_seconds':1200,'per_invocation_bound_seconds':1200},'manager_snapshot':{'mode':status['mode'],'blocked':status['blocked'],'gpu':status['gpu'],'catalog':catalog,'system_stats':system},'sources':[],'jobs':[]}
 for name,ani_name,prefixes,kind in SELECTION:
  folder=OUT/name;folder.mkdir(exist_ok=True);srcfolder=folder/'source';srcfolder.mkdir(exist_ok=True)
  spr=ROOT/'game/Creatures'/(name+'.spr');ani=ROOT/'game/Creatures'/(ani_name+'.ani')
  for p in [spr,ani]:shutil.copy2(p,srcfolder/p.name)
  source={'creature':name,'category':kind,'spr':str(spr),'spr_sha256':sha(spr),'ani':str(ani),'ani_sha256':sha(ani),'copy_spr':str(srcfolder/spr.name),'copy_ani':str(srcfolder/ani.name)}
  palettes,frames=read_spr(spr)
  inventory={}
  for f in frames:inventory.setdefault(f['name'][:-4],[]).append(f)
  source['prefix_inventory']={k:len(v) for k,v in inventory.items()};plan['sources'].append(source)
  groups=[]
  for prefix in prefixes:
   matching=inventory[prefix];nums=[int(f['name'][-4:]) for f in matching]
   assert nums==sorted(nums),('source-order mismatch',name,prefix,nums)
   chosen=matching[:12];assert chosen and all(f['width'] and f['height'] for f in chosen)
   assert all(int(b['name'][-4:])==int(a['name'][-4:])+1 for a,b in zip(chosen,chosen[1:])),('nonconsecutive suffixes',name,prefix)
   groups.append((prefix,chosen,len(matching)))
  allframes=[f for _,fs,_ in groups for f in fs]
  minx=min(f['offset'][0] for f in allframes);miny=min(f['offset'][1] for f in allframes)
  maxx=max(f['offset'][0]+f['width'] for f in allframes);maxy=max(f['offset'][1]+f['height'] for f in allframes)
  cw=max(128,math.ceil((maxx-minx+64)/32)*32);ch=max(128,math.ceil((maxy-miny+64)/32)*32)
  for prefix,chosen,available in groups:
   dest=folder/prefix;dest.mkdir(exist_ok=True);(dest/'source-frames').mkdir(exist_ok=True)
   count=len(chosen);rows=math.ceil(count/4);sheet=Image.new('RGB',(cw*4,ch*rows),BG);meta=[]
   for ordinal,f in enumerate(chosen):
    im=decode(palettes,native_frame(palettes,f));p=dest/'source-frames'/f'{ordinal:02d}.png';im.save(p)
    local=(32+f['offset'][0]-minx,32+f['offset'][1]-miny);origin=((ordinal%4)*cw,(ordinal//4)*ch)
    assert local[0]>=32 and local[1]>=32 and local[0]+im.width<=cw-32 and local[1]+im.height<=ch-32
    sheet.paste(im,(origin[0]+local[0],origin[1]+local[1]),im)
    meta.append({**{k:f[k] for k in ['index','name','width','height','offset','flags']},'ordinal':ordinal,'source_png':str(p),'source_png_sha256':sha(p),'alpha_sha256':hashlib.sha256(im.getchannel('A').tobytes()).hexdigest(),'local_position':local,'cell_origin':origin,'target_2x_size':[im.width*2,im.height*2],'target_2x_offset':[v*2 for v in f['offset']]})
   inp=dest/'input-sheet.png';sheet.save(inp);tw,th=sheet.width*2,sheet.height*2
   if min(tw,th)<64 or max(tw,th)>8192:raise RuntimeError('Manager dimensions unsupported; refusing input compression')
   plan['jobs'].append({'name':name+'-'+prefix,'creature':name,'prefix':prefix,'available_source_frames':available,'selected_frames':count,'selection_note':'All 8 available; no padding/duplicated source frames to reach 12' if count<12 else 'First 12 consecutive suffix frames','source_sha256':source['spr_sha256'],'input':str(inp),'input_sha256':sha(inp),'input_size':sheet.size,'target_size':[tw,th],'cell_size':[cw,ch],'origin_min':[minx,miny],'grid':[4,rows],'margin_native_px':32,'frames':meta,'status':'pending'})
 weights=Path('E:/AI/ComfyUI_windows_portable/ComfyUI_windows_portable/ComfyUI/models/SEEDVR2')
 plan['model_payloads']=[{'path':str(weights/n),'bytes':(weights/n).stat().st_size,'sha256':sha(weights/n)} for n in [MODEL,'ema_vae_fp16.safetensors']]
 plan['coverage']={'creatures':len(SELECTION),'sheets':len(plan['jobs']),'frames':sum(j['selected_frames'] for j in plan['jobs'])}
 verify_sources(plan);write(MANIFEST,plan);return plan
def run():
 parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
 plan=prepare();verify_sources(plan);audit_selectors(plan);print('COVERAGE',plan['coverage'],flush=True)
 if args.prepare_only:return
 invocation_deadline=time.monotonic()+1200
 for task in plan['jobs']:
  if task['status'] in ['complete','failed','dimension-refused']:continue
  if time.monotonic()>invocation_deadline:print('1200s invocation bound; resume saved manifest',flush=True);return
  inp=Path(task['input']);assert sha(inp)==task['input_sha256'];verify_sources(plan)
  if 'job_id' not in task:
   key='mm-seedvr-expanded-20261001-'+task['name']+'-'+task['input_sha256'][:20]
   task['idempotency_key']=key;task['submit_attempt_at']=time.time();write(MANIFEST,plan)
   task['request_fields']={'model':MODEL,'width':task['target_size'][0],'height':task['target_size'][1],'scale':2,'data_url':'PNG base64 of input_sha256 (not duplicated)'}
   task['seed_policy']='Manager image endpoint does not forward seed; no controllable per-job seed exposed. Actual worker default applies.';write(MANIFEST,plan)
   response=api('/workbench/api/upscale/image',{'data_url':'data:image/png;base64,'+base64.b64encode(inp.read_bytes()).decode(),'model':MODEL,'width':task['target_size'][0],'height':task['target_size'][1],'scale':2},key)
   task.update(job_id=response['job_id'],status='submitted',submitted_at=time.time());write(MANIFEST,plan)
   print('SAVED ID',task['name'],task['job_id'],flush=True)
  deadline=min(invocation_deadline,time.monotonic()+1200);last=None
  while True:
   job=api('/api/jobs/'+task['job_id']);state=job['state']
   if state!=last:print(task['name'],state,flush=True);last=state
   if state in ['failed','cancelled','recovery_required']:
    task.update(status='failed',terminal_state=state,error=job.get('error'));write(MANIFEST,plan);break
   if state=='succeeded':
    if not (job.get('result') or {}).get('file'):time.sleep(2);continue
    src=Path(job['result']['file']).resolve();assert src.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve())
    raw=inp.parent/'seedvr-raw.png';shutil.copy2(src,raw)
    with Image.open(raw) as im:actual=list(im.size);im.verify()
    task.update(output=str(raw),output_sha256=sha(raw),actual_output_size=actual,seconds=round(time.time()-task['submitted_at'],2),manager_kind=job['kind'],manager_payload_dimensions=task['target_size'])
    if actual!=task['target_size']:task.update(status='dimension-refused',error='Output shape mismatch; no resizing applied')
    else:task['status']='complete'
    verify_sources(plan);write(MANIFEST,plan);print('SETTLED',task['name'],task['status'],actual,flush=True);break
   if time.monotonic()>deadline:
    task.update(last_polled_state=state,bound_reached_at=time.time());write(MANIFEST,plan);print('BOUND reached; existing ID retained, no duplicate submit',flush=True);return
   time.sleep(3)
 print('COMPLETE',sum(t['status']=='complete' for t in plan['jobs']),'/',len(plan['jobs']),flush=True)
if __name__=='__main__':run()
