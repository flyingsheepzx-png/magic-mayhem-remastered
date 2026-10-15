"""Bounded Celtic map trials. All writes confined to this script's directory.
Python + Pillow + NumPy; no game launch, queue mutation or credentials.
"""
from pathlib import Path
import argparse, base64, hashlib, io, json, time, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[4]
HD=PROJECT/'modernization/assets/hd'
SOURCE=HD/'source-original/Interface/RealmViewer/800x600/Celtic_Map.bmp'
OLD=HD/'pack/Interface/RealmViewer/800x600/Celtic_Map.png'
QUEUE=HD/'hd-queue.json'
BASE='http://127.0.0.1:8790/workbench'
SOURCE_HASH='adffa4c6a0c4c98de1d1af61566df00bba584f22ca2367717921e17b7f14d904'
OLD_HASH='5a0ba1f7e5039c9253f51da7087dba57a168f410da9befa25e7cc69126269ab1'
LANCZOS=Image.Resampling.LANCZOS
CROP=(250,110,650,410)
LOCK=("Edit the provided exact Celtic realm map as a faithful restoration. Keep the same orthographic map viewpoint, framing, scale, land silhouette and color palette. "
      "Lock every coastline, cliff edge, road junction, river, lake, clearing, mountain, forest boundary and existing settlement to its exact reference coordinates and shape. "
      "Preserve the identity, count, footprint and roof orientation of every existing building and landmark. Do not invent missing geography. No new buildings, landmarks, trees outside existing forest, roads, labels, writing, symbols, borders or markers. ")
CONFIG={
 '01-full-conservative':{'size':'1024x768','seed':26093011,'prompt':LOCK+"Improve visual readability with restrained hand-painted fantasy game art: organized tree crowns within the existing canopy, distinct roof planes only on existing buildings, clean rock planes and softly modeled hills. Remove granular speckles and repetitive microtexture. Prefer medium-sized coherent shapes and clear silhouettes over sharp noise. Retain the original atmospheric lighting and muted greens, brown rock and dark blue sea. This is an edit of the reference, not a redesigned map."},
 '02-full-readable':{'size':'2400x1792','seed':26093012,'prompt':LOCK+"Repaint surface shading only as polished readable hand-painted strategy-game terrain. Simplify chaotic tiny marks into calm broad grass gradients. Make existing forest clusters readable with a few grouped canopy forms and soft shadow separations; clarify the existing settlement roofs and walls without adding structures. Give existing mountains and cliffs clear layered rock planes. Roads and rivers must follow the original path exactly. No photographic grain, pebble carpet, stippling, gritty noise, oversharpened outlines or repeated texture stamps. Preserve the original map rather than drawing a new one."},
 '03-context-crop':{'size':'1024x768','seed':26093013,'crop':CROP,'prompt':LOCK+"This is a contextual rectangular crop of the map, not a complete island: keep all features crossing the crop edges in precisely the same places. Refine only painted surface details at higher clarity. Keep the existing tiny orange-roof settlement precisely in its original place and footprint; make its original roof planes easier to distinguish. Preserve the lake shape, roads and forest contours. Consolidate forest noise into readable grouped crowns and smooth grass shading. No new individual house or landmark, no enlarged settlement, no new coastline, no text. Avoid intricate random detail and strongly sharpened speckles."}
}
NEGATIVE='new landmarks, new houses, changed building count, shifted roads, shifted coast, displaced rivers, enlarged village, labels, text, letters, symbols, photo texture, grain, speckles, tiled microtexture, changed perspective'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(name,data): (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load_json(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def api(route,payload=None):
 req=urllib.request.Request(BASE+route,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
def verify():
 assert SOURCE.is_file() and sha(SOURCE)==SOURCE_HASH,'Unknown source hash'
 assert OLD.is_file() and sha(OLD)==OLD_HASH,'Old output hash changed'
 q=json.loads(QUEUE.read_text(encoding='utf-8'))
 rec=next(r for r in q['records'] if r['source']=='Interface/RealmViewer/800x600/Celtic_Map.bmp')
 assert rec['source_sha256']==SOURCE_HASH
 return {'source_path':str(SOURCE),'source_sha256':sha(SOURCE),'old_path':str(OLD),'old_sha256':sha(OLD),'queue_sha256':sha(QUEUE),'queue_record':rec}
def prepare():
 evidence=verify(); write_json('input-provenance.json',evidence)
 source=Image.open(SOURCE).convert('RGB'); source.save(ROOT/'source-800x600.png')
 source.resize((1920,1440),LANCZOS).save(ROOT/'lanczos-1920x1440.png')
 source.resize((1920,1440),Image.Resampling.NEAREST).save(ROOT/'source-nearest-1920x1440.png')
 Image.open(OLD).save(ROOT/'old-qwen-1920x1440.png')
 source.crop(CROP).save(ROOT/'context-reference-400x300.png')
 write_json('trial-settings.json',{'model':'Qwen-Image 2.1','endpoint':BASE+'/api/keyframe2/jobs','steps':40,'quality':'quality','per_round':1,'transparent':False,'official_prompt_enhance':False,'negative_prompt':NEGATIVE,'candidates':CONFIG,'note':'No denoise/ControlNet parameter assumed: API exposes image reference and text constraints. Images encoded PNG in-memory; no token stored.'})
 print('Prepared; source and old output hashes verified',flush=True)
def generate(name):
 verify(); cfg=CONFIG[name]; result=ROOT/(name+'-raw.png'); manifest_name=name+'-call.json'
 if result.exists(): print('Existing result: no resubmission',name,flush=True); return
 if (ROOT/manifest_name).exists() and load_json(manifest_name).get('terminal_status') in {'failed','canceled','cancelled','interrupted'}: raise RuntimeError('Recorded terminal job; no automatic resubmission')
 image=Image.open(SOURCE).convert('RGB')
 if cfg.get('crop'): image=image.crop(cfg['crop'])
 buf=io.BytesIO(); image.save(buf,format='PNG'); ref=buf.getvalue()
 health=api('/api/keyframe2/status'); engine=health.get('engines',{}).get('qwen21',{})
 assert engine.get('ok') and engine.get('assets_ready'),'Qwen21 unavailable; do not substitute'
 payload={'engine':'qwen21','reference_images':['data:image/png;base64,'+base64.b64encode(ref).decode()], 'prompt':cfg['prompt'],'negative_prompt':NEGATIVE,'nickname':'MM quality-review-1.1 bounded '+name,'quality':'quality','size':cfg['size'],'steps':40,'seed':cfg['seed'],'per_round':1,'official_prompt_enhance':False,'transparent':False}
 if (ROOT/manifest_name).exists():
  record=load_json(manifest_name); job_id=record['manager_job_id']; print('Resume',job_id,flush=True)
 else:
  job_id=api('/api/keyframe2/jobs',payload)['job']['id']
  record={'candidate':name,'manager_job_id':job_id,'source_sha256':SOURCE_HASH,'reference_png_sha256':hashlib.sha256(ref).hexdigest(),'reference_size':image.size,'reference_crop':cfg.get('crop'),'request':{k:v for k,v in payload.items() if k!='reference_images'},'health_engine':{k:engine.get(k) for k in ['ok','assets_ready','model','license']},'submitted_local':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'observations':[]}
  write_json(manifest_name,record)
 print('OWNED QWEN JOB',name,job_id,flush=True); start=time.monotonic(); last=None; next_log=0
 try:
  while True:
   job=api('/api/keyframe2/jobs/'+job_id); job=job['job']
   initializing=job.get('status') in {'queued','pending','running','canceled','cancelled','interrupted'} and not job.get('prompt')
   if not initializing: assert job.get('engine')=='qwen21' and job.get('prompt')==cfg['prompt'],'Job identity mismatch'
   status=job.get('status'); phase=job.get('phase_code') or job.get('phase'); state=(status,phase)
   if state!=last or time.monotonic()>next_log:
    obs={'status':status,'phase':phase,'elapsed_poll_seconds':round(time.monotonic()-start,1)}; record['observations'].append(obs); write_json(manifest_name,record); print(obs,flush=True); last=state; next_log=time.monotonic()+30
   if status in {'completed','failed','canceled','cancelled','interrupted'}: break
   if time.monotonic()-start>2400:
    api('/api/keyframe2/jobs/'+job_id+'/cancel',{}); raise TimeoutError('Canceled only owned job '+job_id)
   time.sleep(2)
 except KeyboardInterrupt:
  api('/api/keyframe2/jobs/'+job_id+'/cancel',{}); raise
 record['terminal_status']=status; record['poll_wall_seconds']=round(time.monotonic()-start,2)
 if status!='completed':
  record['failure_phase']=phase; write_json(manifest_name,record); raise RuntimeError('Qwen failed '+str(phase))
 media=next(s['primary'] for s in job['sequences'] if s.get('primary'))
 url=urllib.parse.urljoin('http://127.0.0.1:8790',media['url']); assert url.startswith(BASE+'/api/')
 with urllib.request.urlopen(url,timeout=60) as r: raw=r.read()
 assert raw.startswith(b'\x89PNG\r\n\x1a\n'); result.write_bytes(raw)
 gen=Image.open(result).convert('RGB'); record.update(output_sha256=sha(result),actual_output_size=gen.size,result_gateway_url=url,completed_local=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
 write_json(manifest_name,record)
 target=(960,720) if cfg.get('crop') else (1920,1440)
 gen.resize(target,LANCZOS).save(ROOT/(name+'-target.png'))
 print('SAVED',result.name,gen.size,record['output_sha256'],flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['prepare','generate']); parser.add_argument('--candidate',choices=list(CONFIG)); a=parser.parse_args()
 if a.mode=='prepare': prepare()
 else:
  assert a.candidate; generate(a.candidate)



