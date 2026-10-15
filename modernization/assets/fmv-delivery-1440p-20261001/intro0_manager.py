"""Owned, authenticated FIFO SeedVR2 intro0 job; safe resumable submission."""
import os
import base64,json,time,urllib.request,sys
from pathlib import Path
from deliver import ROOT,OLD,sha,probe
BASE='http://127.0.0.1:8790'
STATE=ROOT/'intro0-manager.json'
MODEL='seedvr2_ema_7b_sharp_fp8_e4m3fn.safetensors'
def api(route,data=None,key=None):
 token=json.loads(Path(os.environ['MM_LOCAL_MODEL_CREDENTIAL']).read_text(encoding='utf-8'))['token']
 h={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
 if key:h['Idempotency-Key']=key
 req=urllib.request.Request(BASE+route,headers=h,data=None if data is None else json.dumps(data).encode())
 with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)
def save(s):
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(s,indent=2),encoding='utf-8');tmp.replace(STATE)
def main():
 if STATE.exists():s=json.loads(STATE.read_text(encoding='utf-8'))
 else:
  status=api('/api/status');assert status['mode']=='managed'
  cat=api('/workbench/api/upscale/models');assert any(x['id']==MODEL and x['installed'] for x in cat['models'])
  inp=OLD/'1920x1440/inputs/intro0.mp4';meta=probe(inp,True)
  assert int(next(x for x in meta['streams'] if x['codec_type']=='video')['nb_read_frames'])==1756
  models=list(Path('E:/AI').glob('ComfyUI_windows_portable/ComfyUI_windows_portable/ComfyUI/models/SEEDVR2/'+MODEL));assert len(models)==1
  s={'input':str(inp),'input_sha256':sha(inp),'model':MODEL,'model_path':str(models[0]),'model_sha256':sha(models[0]),'idempotency_key':'mm-fmv-intro0-1440p-'+sha(inp),'request':{'model':MODEL,'width':2560,'height':1440,'scale':4},'effective_profile':{'batch_size':9,'uniform_batch_size':True,'chunk_size':180,'temporal_overlap':3,'color_correction':'lab','tensor_offload_device':'cpu','vae_encode_tiled':True,'vae_decode_tiled':True,'seed':42,'seed_source':'installed CLI default, Manager does not expose seed','input_noise_scale':0,'latent_noise_scale':0},'stage':'prepared'};save(s)
 if not s.get('job_id'):
  assert sha(s['input'])==s['input_sha256']
  payload={**s['request'],'data_url':'data:video/mp4;base64,'+base64.b64encode(Path(s['input']).read_bytes()).decode()}
  assert len(json.dumps(payload).encode())<32*1024*1024
  s['request_body_bytes']=len(json.dumps(payload).encode());s['stage']='submitting';save(s)
  answer=api('/workbench/api/upscale/video',payload,s['idempotency_key']);s['job_id']=answer['job_id'];s['stage']='submitted';save(s)
 print('OWNED_JOB',s['job_id'],flush=True)
 deadline=time.monotonic()+1200
 while time.monotonic()<deadline:
  job=api('/api/jobs/'+s['job_id']);s['latest']=job;save(s)
  print('STATUS',job['state'],job.get('progress'),flush=True)
  if job['state']=='succeeded':
   out=Path(job['result']['file']);meta=probe(out,True);v=next(x for x in meta['streams'] if x['codec_type']=='video')
   assert (v['width'],v['height'])==(2560,1440),(v['width'],v['height'])
   assert int(v['nb_read_frames'])==1756,v.get('nb_read_frames')
   s['result']=str(out);s['result_sha256']=sha(out);s['stage']='inference_verified';save(s);print('READY',out,flush=True);return
  if job['state'] in ('failed','cancelled','recovery_required'):raise RuntimeError(job.get('error') or job['state'])
  time.sleep(30)
 print('BOUND_REACHED_RESUME_SAME_ID',s['job_id'],flush=True)
if __name__=='__main__':main()
