"""Isolated CPU preparation/evaluation; every inference uses Manager FIFO.
Run with system Python + Pillow/numpy. Resume: python run_review.py
No runtime writes; no model downloads; owned job IDs persisted before polling.
"""
import os
from pathlib import Path
import sys,json,hashlib,base64,urllib.request,urllib.parse,time,subprocess,shutil
import numpy as np
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'modernization/tools'))
from spr_assets import read_spr,decode
BASE='http://127.0.0.1:8790'
CRED=Path(os.environ['MM_LOCAL_MODEL_CREDENTIAL'])
FF=Path('E:/AI/LosslessCut/resources/ffmpeg.exe')
PLAN=OUT/'manifest.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save():
 p=PLAN.with_suffix('.tmp');p.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');p.replace(PLAN)
def api(path,payload=None,key=None,comfy=False,raw=False):
 headers={'Authorization':'Bearer '+json.loads(CRED.read_text())['token'],'Content-Type':'application/json'}
 if key:headers['Idempotency-Key']=key
 url=('http://127.0.0.1:8791' if comfy else BASE)+path
 req=urllib.request.Request(url,headers=headers,data=None if payload is None else json.dumps(payload).encode())
 with urllib.request.urlopen(req,timeout=45) as r:return r.read() if raw else json.load(r)
def data(p,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def ff(args):subprocess.run([str(FF),'-hide_banner','-loglevel','error',*args],check=True,creationflags=0x08000000)
if PLAN.exists():plan=json.loads(PLAN.read_text())
else:
 (OUT/'sources').mkdir(exist_ok=True);(OUT/'inputs').mkdir(exist_ok=True)
 src=ROOT/'game/Creatures/Bat.spr';ani=ROOT/'game/Creatures/bat.ani'
 for p in [src,ani]:shutil.copy2(p,OUT/'sources'/p.name)
 palettes,frames=read_spr(src);selected=[f for f in frames if f['name'].startswith('AALF')][:6]
 assert len(selected)==6
 minx=min(f['offset'][0] for f in selected);miny=min(f['offset'][1] for f in selected)
 atlas=Image.new('RGB',(384,256),(48,48,56));rows=[]
 for i,f in enumerate(selected):
  im=decode(palettes,f);im.save(OUT/'sources'/f'{i:02d}.png')
  pos=(24+f['offset'][0]-minx,24+f['offset'][1]-miny)
  canvas=Image.new('RGB',(128,128),(48,48,56));canvas.paste(im,pos,im);canvas.save(OUT/'inputs'/f'{i:02d}.png')
  atlas.paste(canvas,((i%3)*128,(i//3)*128))
  rows.append({**{k:f[k] for k in ['index','name','width','height','offset','flags']},'position':pos,'source_png_sha256':sha(OUT/'sources'/f'{i:02d}.png')})
 atlas.save(OUT/'inputs/atlas.png')
 q=Image.new('RGB',(1024,1024),(48,48,56));q.paste(atlas.resize((1024,683),Image.Resampling.NEAREST),(0,170));q.save(OUT/'inputs/qwen.png')
 ff(['-y','-framerate','8','-i',str(OUT/'inputs/%02d.png'),'-frames:v','6','-c:v','libx264rgb','-crf','0',str(OUT/'inputs/sequence.mp4')])
 catalog=api('/workbench/api/upscale/models');nodes=api('/object_info/UpscaleModelLoader',comfy=True)
 plan={'scope':'offline six AALF bat frames; ANI semantics/timing unverified; no runtime/UI/art-plan modifications','source':str(src),'source_sha256':sha(src),'ani_sha256':sha(ani),'frames':rows,'catalog':catalog,'comfy_upscale_registry':nodes,'jobs':[]}
 seed=next(m['id'] for m in catalog['models'] if m['engine']=='SeedVR2')
 plan['jobs']=[{'name':'seedvr-sheet','model':seed,'mode':'image','input':'atlas.png'}, {'name':'pixelperfect-sheet','model':'4x-PixelPerfectV4.pth','mode':'comfy','input':'atlas.png'}, {'name':'qwen-sheet','model':'qwen21','mode':'qwen','input':'qwen.png'}]
 for m in catalog['models']:
  if m['installed']:plan['jobs'].append({'name':m['id'].split('.')[0],'model':m['id'],'mode':'video','input':'sequence.mp4'})
 for j in plan['jobs']:j['input_sha256']=sha(OUT/'inputs'/j['input']);j['status']='pending'
 save()
for j in plan['jobs']:
 if j['status'] in ['complete','failed']:continue
 inp=OUT/'inputs'/j['input'];assert sha(inp)==j['input_sha256']
 dest=OUT/j['name'];dest.mkdir(exist_ok=True)
 if 'job_id' not in j:
  key='mm-creature-20260930-'+j['name']+'-'+j['input_sha256'][:16]
  j['idempotency_key']=key;save()
  try:
   if j['mode'] in ['image','video']:
    w,h=(768,512) if j['mode']=='image' else (256,256)
    response=api('/workbench/api/upscale/'+j['mode'],{'data_url':data(inp,'video/mp4' if j['mode']=='video' else 'image/png'),'model':j['model'],'width':w,'height':h,'scale':2},key)
    jid=response['job_id']
   elif j['mode']=='qwen':
    payload={'engine':'qwen21','reference_images':[data(inp)],'prompt':'Restore this exact six-frame bat animation sprite sheet. Preserve every cell, pose, wing membrane, limb, face, viewpoint and background. Enhance fine detail only. Do not add limbs, move frames, change anatomy or invent objects. Keep the grey margins uniform.','negative_prompt':'extra limbs, changed pose, merged frames, new objects, text, watermark','nickname':'creature sequence isolated review','quality':'quality','size':'1024x1024','steps':12,'seed':260930,'per_round':1,'official_prompt_enhance':False,'transparent':False}
    (dest/'request.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='reference_images'},indent=2))
    jid=api('/workbench/api/keyframe2/jobs',payload,key)['job']['id']
   else:
    boundary='mmcreatureupload';raw=inp.read_bytes()
    body=('--'+boundary+'\r\nContent-Disposition: form-data; name="image"; filename="creature-review-atlas.png"\r\nContent-Type: image/png\r\n\r\n').encode()+raw+('\r\n--'+boundary+'--\r\n').encode()
    headers={'Authorization':'Bearer '+json.loads(CRED.read_text())['token'],'Content-Type':'multipart/form-data; boundary='+boundary}
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8791/upload/image',headers=headers,data=body),timeout=45) as r:upload=json.load(r)
    image=upload['subfolder']+'/'+upload['name'] if upload.get('subfolder') else upload['name']
    graph={'1':{'class_type':'LoadImage','inputs':{'image':image}},'2':{'class_type':'UpscaleModelLoader','inputs':{'model_name':j['model']}},'3':{'class_type':'ImageUpscaleWithModel','inputs':{'image':['1',0],'upscale_model':['2',0]}},'4':{'class_type':'SaveImage','inputs':{'images':['3',0],'filename_prefix':'creature-sequence-review'}}}
    (dest/'workflow.json').write_text(json.dumps(graph,indent=2))
    jid=api('/api/jobs',{'kind':'comfy','payload':{'prompt':graph}},key)['id']
   j.update(job_id=jid,status='submitted',submitted_at=time.time());save();print('SAVED',j['name'],jid,flush=True)
  except Exception as e:
   j.update(status='failed',error=str(e));save();print('SUBMIT FAILED',j['name'],str(e),flush=True);continue
 deadline=time.monotonic()+1200;last=None
 while True:
  if j['mode']=='qwen':
   result=api('/workbench/api/keyframe2/jobs/'+j['job_id'])['job'];state=result['status']
  else:result=api('/api/jobs/'+j['job_id']);state=result['state']
  if state!=last:print(j['name'],state,flush=True);last=state
  if state in ['failed','cancelled','canceled','recovery_required']:
   j.update(status='failed',error=result.get('error') or result.get('phase'),terminal_state=state);save();break
  if state in ['succeeded','completed']:
   if j['mode']=='qwen':
    primary=next(s['primary'] for s in result['sequences'] if s.get('primary'));url=urllib.parse.urljoin(BASE,primary['url']);assert url.startswith(BASE+'/workbench/api/')
    output=dest/'raw.png';output.write_bytes(api(url[len(BASE):],raw=True))
   elif j['mode']=='comfy':
    hist=result.get('result',{}).get('history')
    if not hist:time.sleep(2);continue
    img=hist['outputs']['4']['images'][0];output=dest/'raw.png';output.write_bytes(api('/view?'+urllib.parse.urlencode(img),comfy=True,raw=True))
   else:
    file=Path(result['result']['file']).resolve();assert file.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve());output=dest/('raw.mp4' if j['mode']=='video' else 'raw.png');shutil.copy2(file,output)
   j.update(status='complete',output=str(output),output_sha256=sha(output),seconds=round(time.time()-j['submitted_at'],2));save();break
  if time.monotonic()>deadline:
   print('Bound reached; resume existing saved job ID',flush=True);sys.exit(2)
  time.sleep(3)
print('Inference phase settled',flush=True)
