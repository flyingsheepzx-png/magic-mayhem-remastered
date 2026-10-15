"""Refresh honest provenance and full-size proof frames without inference."""
import json,subprocess
from pathlib import Path
from deliver import ROOT,SRC,FF,sha
def main():
 man=ROOT/'manifest.json';m=json.loads(man.read_text(encoding='utf-8'));state=json.loads((ROOT/'intro0-manager.json').read_text(encoding='utf-8'))
 m['films']['intro0'].update(method='new SeedVR2 4x 2560x1440 inference; original held-frame PTS restored',manager_job_id=state['job_id'],model_sha256=state['model_sha256'],raw_project_copy=state['project_raw_copy'],raw_project_sha256=state['project_raw_sha256'])
 historical={'Medieval':'f4f7c8cd4fe64d05974c99983c601f50','Intro1':'7ad902b4ccaa4072a91da685c4b79ae7'}
 for n,j in historical.items():m['films'][n]['historical_seedvr_manager_job_id']=j
 m['policy']['new_gpu_submissions']=1;m['policy']['preserved_original_sources']=True
 man.write_text(json.dumps(m,indent=2,ensure_ascii=False),encoding='utf-8')
 for name,second in [('Medieval',17),('Intro1',35),('intro0',40),('Celtic',3),('Greek',3)]:
  subprocess.run([FF,'-v','error','-y','-ss',str(second),'-i',str(ROOT/(name+'.mp4')),'-frames:v','1',str(ROOT/(name+'-2560x1440.png'))],check=True,timeout=120)
 cards=[]
 for n in ('Medieval','Intro1','intro0','Celtic','Greek'):
  r=m['films'][n];cards.append(f'<h2>{n}</h2><p>{r["method"]}<br>2560×1440 · {r["frames"]} frames · {r["duration"]}s · {r["bytes"]/1048576:.1f}MiB</p><video controls preload="metadata" src="{n}.mp4" poster="{n}-2560x1440.png"></video><p><a href="{n}-2560x1440.png">Open original full 2560×1440 PNG</a></p>')
 (ROOT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>FMV 1440p delivery</title><style>body{background:#151515;color:#eee;font:17px sans-serif;margin:30px}video{max-width:100%;width:1280px}a{color:#adf}</style><h1>2560×1440 H.264 delivery</h1><p>No autoplay. Full-size stills linked separately.</p>'+''.join(cards),encoding='utf-8')
 for n,r in m['films'].items():assert sha(r['original'])==r['original_sha256'];assert sha(r['mp4'])==r['mp4_sha256'];assert sha(r['master'])==r['master_sha256']
 print('PROVENANCE_AND_SOURCES_REVERIFIED',flush=True)
if __name__=='__main__':main()
