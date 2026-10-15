"""User-authorized test19 then immediate test18 reload, read-only diagnostics."""
import argparse,ctypes,time,os,threading
import compare_remastered_ui_11 as c
from probe_11_close_wait import chains

def run(name):
 ctypes.windll.user32.SetProcessDPIAware();p=c.CANDIDATE
 identity=c.verify_package(p,'1.1',c.sha(p/'manifest.json'))
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 s=c.session_class()(identity,p/'runtime',out/'1.1',100)
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
   now=time.time_ns();os.utime(s.lab/'Save/test19.sav',ns=(now,now));os.utime(s.lab/'Save/test18.sav',ns=(now-1000000,now-1000000))
   worker=threading.Thread(target=sample,daemon=True);worker.start()
   load('test19','main');load('test18','battle')
   phase[0]='test18-observe';time.sleep(2);s.message(0)
   s.result['reload_sequence']='completed';s.shot('test18-after-reload',False)
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
   stop.set()
   if worker:worker.join(timeout=2)
   c.write_json(out/'timeline.json',timeline)
 print(out,s.result.get('reload_sequence'),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();run(a.name)
