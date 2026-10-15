"""Resume exactly the owned intro0 job, then complete the remaining CPU deliveries."""
import json,time,subprocess
from pathlib import Path
from deliver import ROOT,OLD,FF,deliver,sha,probe,run
from intro0_manager import api,STATE,save
def main():
 deadline=time.monotonic()+3*3600
 while time.monotonic()<deadline:
  s=json.loads(STATE.read_text(encoding='utf-8'));job=api('/api/jobs/'+s['job_id'])
  if job['state']=='succeeded':
   output=Path(job['result']['file']);p=probe(output,True);v=next(x for x in p['streams'] if x['codec_type']=='video')
   assert (v['width'],v['height'],int(v['nb_read_frames']))==(2560,1440,1756)
   s.update(result=str(output),result_sha256=sha(output),stage='inference_verified',latest=job);save(s)
   deliver('intro0',str(output),True);break
  if job['state'] in ('failed','cancelled','recovery_required'):raise RuntimeError(job)
  print('OWNED_PENDING',s['job_id'],job['state'],flush=True);time.sleep(30)
 else:raise TimeoutError('3 hour collector bound; job remains owned, resume without resubmit')
 # Only after all three SeedVR films are complete, use the preserved H3 edits.
 celtic=OLD/'h3-celtic/video-reconstruction/Celtic-H3-SeedVR2-H3-splice-preview.mp4'
 greek=OLD/'h3-greek/video-reconstruction/Greek-H3-two-shot-white-splice-preview.mp4'
 for name,p in [('Celtic',celtic),('Greek',greek)]:
  # Crop the shared 1920x1080 picture from the old 1920x1440 canvas.
  temp=ROOT/f'{name}-crop-source.mkv'
  if not temp.exists():run([FF,'-v','warning','-y','-i',str(p),'-map','0:v:0','-vf','crop=1920:1080:0:180','-c:v','libx264','-preset','fast','-crf','0','-fps_mode','passthrough',str(temp)],ROOT/f'{name}-crop.log')
  deliver(name,str(temp))
  man=ROOT/'manifest.json';m=json.loads(man.read_text(encoding='utf-8'));row=m['films'][name];row.update(mixed_source=str(p),mixed_source_sha256=sha(p),method='reused H3 opening / SeedVR2 middle / H3 ending' if name=='Celtic' else 'reused latest H3 two-shot edit with portal whiteout cut; no SeedVR2 middle',creative_geometry_change=True);man.write_text(json.dumps(m,indent=2),encoding='utf-8')
 # Full-size proof frames and a browsable video gallery (no downscaled-only QA).
 m=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'));cards=[]
 for name in ('Medieval','Intro1','intro0','Celtic','Greek'):
  row=m['films'][name];still=ROOT/(name+'-2560x1440.png')
  run([FF,'-v','error','-y','-ss',str(min(5,float(row['duration'])/2)),'-i',row['mp4'],'-frames:v','1',str(still)],ROOT/(name+'-still.log'))
  cards.append(f'<h2>{name}</h2><p>{row["method"]} · {row["frames"]} frames · {row["duration"]} s</p><video controls preload="metadata" src="{name}.mp4"></video><p><a href="{still.name}">Full 2560×1440 still</a></p>')
 html='<!doctype html><meta charset="utf-8"><title>FMV 1440p delivery</title><style>body{background:#151515;color:#eee;font:17px sans-serif;margin:30px}video{max-width:100%;width:1280px}a{color:#adf}</style><h1>2560×1440 H.264 · preserved audio and timing</h1>'+''.join(cards)
 (ROOT/'index.html').write_text(html,encoding='utf-8');print('ALL_DELIVERY_VERIFIED',flush=True)
if __name__=='__main__':main()
