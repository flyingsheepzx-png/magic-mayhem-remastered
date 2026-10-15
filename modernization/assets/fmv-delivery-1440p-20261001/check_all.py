"""After CPU delivery settles, exercise every film in an isolated owned game."""
import json,subprocess,sys,time,shutil
from pathlib import Path
from deliver import ROOT,sha
sys.path.insert(0,str(ROOT.parents[2]/'modernization/tools'))
import wide169_trial as w
def wait_idle(limit=1200):
 deadline=time.monotonic()+limit
 while time.monotonic()<deadline:
  if not any(n.startswith(('chaos','magicmayhem')) for _,_,n in w.processes(w.configured_kernel())):return
  print('EXTERNAL_GAME_ACTIVE_WAITING',flush=True);time.sleep(30)
 raise TimeoutError('External game active; never interrupt it. Resume check_all.py')
def main():
 deadline=time.monotonic()+3*3600
 while time.monotonic()<deadline:
  manifest=ROOT/'manifest.json'
  if manifest.exists():
   m=json.loads(manifest.read_text(encoding='utf-8'))
   if all(m['films'].get(n,{}).get('verified') for n in ('Medieval','Intro1','intro0','Celtic','Greek')):break
  time.sleep(30)
 else:raise TimeoutError('Delivery still pending; preserve owned job and resume')
 script=ROOT/'check_game.py';records=[]
 for label,first,second,seconds in [('final-intro0-greek','intro0','Greek',145),('final-celtic-medieval','Celtic','Medieval',70),('final-intro1','Intro1','Celtic',85)]:
  wait_idle()
  folder=ROOT/'playback-checks'/label
  if not (folder/'accepted.json').exists():
   # Retain failed attempts; new attempt directory rather than overwriting.
   if folder.exists():label+='-'+str(int(time.time()));folder=ROOT/'playback-checks'/label
   subprocess.run([sys.executable,str(script),'--label',label,'--first',first,'--second',second,'--seconds',str(seconds)],check=True,timeout=seconds+60)
   events=[json.loads(x) for x in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines() if x]
   assert not any(x['event'] in ('mf_error','mf_command_error','fallback_avi') for x in events),events
   ends=[x for x in events if x['event']=='ended'];assert len(ends)>=2,(label,'unexpected skip or incomplete playback',events)
   audio=json.loads((folder/'audio-session.json').read_text(encoding='utf-8'));assert audio['peak']>0.0001 and not audio['muted']
   screenshots=json.loads((folder/'report.json').read_text(encoding='utf-8'))['captures'];assert sum(x['std_rgb']>3 for x in screenshots)>=2
   accepted={'first':first,'second':second,'natural_ends':len(ends),'events':str(folder/'events.jsonl'),'events_sha256':sha(folder/'events.jsonl'),'audio':audio,'shared_runtime_modified':False,'trigger_scope':'startup calls exercise both files through shared native movie detour; campaign realm transition not driven'}
   (folder/'accepted.json').write_text(json.dumps(accepted,indent=2),encoding='utf-8')
  records.append(json.loads((folder/'accepted.json').read_text(encoding='utf-8')))
 for name in ('Medieval','Intro1','intro0','Celtic','Greek'):
  source=ROOT/(name+'.mp4');target=ROOT/'playtest/runtime/FMV'/(name+'.mp4');shutil.copy2(source,target);assert sha(source)==sha(target)
 (ROOT/'playback-validation.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('ALL_FIVE_ACTUAL_PLAYBACK_VALIDATED',flush=True)
if __name__=='__main__':main()
