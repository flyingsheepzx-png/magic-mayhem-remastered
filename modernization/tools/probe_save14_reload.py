"""Owned save14 gameplay/reload reproduction with first-exception capture."""
import argparse,ctypes,time,os,threading,shutil,subprocess
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
import compare_remastered_ui_11 as c
from probe_11_close_wait import chains

def run(name,candidate=None,active=False,observe=True):
 ctypes.windll.user32.SetProcessDPIAware()
 p=base.DEST;binary=candidate or c.ROOT/'modernization/build/remastered-1.1-dynamic-wait-v2/candidate.exe'
 if candidate:
  assert all(resources(binary)[i]==resources(p/base.ENTRY)[i] for i in [101,103])
 else:assert resources(binary)==resources(p/base.ENTRY)
 identity=dict(version='1.1',package=str(p),launcher_name=base.ENTRY,launcher_sha256=c.sha(p/base.ENTRY),engine_sha256=c.ENGINES['1.1'])
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav')
 shutil.copy2(binary,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(binary)
 s=c.session_class()(identity,rt,out/'1.1',100)
 observer=None;av=out/'exception';av.mkdir()
 timeline=[];stop=threading.Event();worker=None;phase=['startup']
 def sample():
  while not stop.is_set():
   try:
    timeline.append(dict(t=time.perf_counter(),phase=phase[0],frame=s.i(0x641fbc),mode=s.i(0x6903e8),controls=s.i(0x642c68),units=s.i(0x6df180),unit_base=s.i(0x6def58),world=s.i(0x6c54dc),surface=[s.i(0x6a49f0),s.i(0x6a49f4)]))
   except Exception as e:timeline.append(dict(t=time.perf_counter(),phase=phase[0],error=str(e)));break
   stop.wait(.05)
 def wait_list():
  deadline=time.monotonic()+4
  while time.monotonic()<deadline:
   row=next((r for r in s.controls() if r['vtable']=='0x5c6db8'),None)
   if row:return row['rect']
   time.sleep(.05)
  c.write_json(out/'unexpected-controls.json',s.controls());raise RuntimeError('Load list absent')
 def load(name,menu):
  phase[0]=name+'-open'
  if menu=='main':s.click_base(640,456)
  else:
   s.key(0x1b);time.sleep(.15)
   c.write_json(out/'escape-controls.json',s.controls())
   s.click_base(640,240)
  rect=wait_list()
  rows=sorted((s.lab/'Save').glob('*.sav'),key=lambda f:f.stat().st_mtime_ns,reverse=True)
  idx=[f.stem.lower() for f in rows].index(name)
  h=s.i(s.i(0x656680)+16)+2;x=(rect[0]+rect[2])//2;y=int(rect[1]+(idx+.5)*h)
  assert y<rect[3]
  c.write_json(out/(name+'-list.json'),dict(rows=[f.stem for f in rows],selected=idx,rect=rect,click=[x,y],fixture_sha256=c.sha(s.lab/'Save'/f'{name}.sav')))
  for ev in [0x200,0x201,0x202]:s.message(ev,x,y);time.sleep(.09)
  phase[0]=name+'-submit';s.click_base(328,666)
  phase[0]=name+'-wait'
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   s.message(0)
   controls=s.controls()
   if name=='test19' and any(r['pointer']=='0x659d9d' for r in controls) and not any(r['vtable']=='0x5c6db8' for r in controls):
    c.write_json(out/(name+'-ready.json'),dict(t=time.perf_counter(),page='campaign',controls=controls));return
   if any(r['vtable']=='0x5c6a54' and r['rect']==[0,0,1280,720] for r in controls) and not any(r['vtable']=='0x5c6db8' for r in controls) and s.i(0x6df180)>0:
    base=s.i(0x6def58)
    if base and s.i(base+4):
     c.write_json(out/(name+'-ready.json'),dict(t=time.perf_counter(),grid=[s.i(base+o) for o in [8,12,16]],units=s.i(0x6df180),base=base,controls=controls));return
   time.sleep(.05)
  raise RuntimeError(name+' load deadline')
 with s:
  try:
   if observe:
    helper=c.ROOT/'modernization/build/hang-dump-x86/capture_first_av_x86.exe'
    observer=subprocess.Popen([str(helper),str(s.pid),str((rt/'Chaos-Wide169-engine.exe').resolve()),str(av.resolve()),'65'],stdout=(av/'helper.txt').open('w'),stderr=subprocess.STDOUT)
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
     if (av/'helper.txt').exists() and 'ATTACHED PID' in (av/'helper.txt').read_text():break
     time.sleep(.1)
    else:raise RuntimeError('Exception observer attachment failed')
   worker=threading.Thread(target=sample,daemon=True);worker.start()
   load('14','main')
   for cycle in range(3):
    phase[0]='operate-'+str(cycle);s.click_base(1218,650) if active else s.click_base(30,30);time.sleep(.15)
    before=s.i(0x6def58);before_world=[s.i(before+o) for o in [0x14,0x18,0x1c]]
    if active:assert s.i(before+0x68)==1,'Hero selection not confirmed'
    s.click_base(700,380,right=active);time.sleep(.8)
    operation=dict(before=before_world,after=[s.i(before+o) for o in [0x14,0x18,0x1c]],order=s.i(before+0x5ec),action=s.i(before+0x5fc),goal=[s.i(before+o) for o in [0x96b,0x96f,0x973]])
    if active:
     s.key(ord('W'));time.sleep(.2);operation['spell_target_mode']=s.i(0x6903e8)
     s.click_base(640,370);time.sleep(.7);operation['after_cast_mode']=s.i(0x6903e8)
     operation['after_cast_action']=s.i(before+0x5fc)
     if s.i(0x6903e8)==2:s.click_base(640,370,right=True)
    c.write_json(out/('operation-'+str(cycle)+'.json'),operation)
    load('14','battle')
   phase[0]='save14-observe';time.sleep(2);s.message(0)
   s.result['reload_sequence']='completed';s.shot('save14-after-reload',False)
  except Exception as e:
   phase[0]='failure';s.result['reload_sequence']='failed';s.result['reload_error']=str(e)
   c.write_json(out/'wait-chains.json',chains(s.pid))
   try:
    c.write_json(out/'failure-controls.json',s.controls());s.shot('failure',False)
   except Exception as capture_error:s.result['failure_capture_error']=str(capture_error)
   time.sleep(2)
   c.write_json(out/'wait-chains-later.json',chains(s.pid))
   print('reproduction failure',str(e),flush=True)
  finally:
   (av/'stop.capture').touch()
   if observer:observer.wait(timeout=20)
   stop.set()
   if worker:worker.join(timeout=2)
   c.write_json(out/'timeline.json',timeline)
 print(out,s.result.get('reload_sequence'),flush=True)

if __name__=='__main__':
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--candidate',type=Path);p.add_argument('--active-actions',action='store_true');p.add_argument('--no-observer',action='store_true');a=p.parse_args();run(a.name,a.candidate,a.active_actions,not a.no_observer)
