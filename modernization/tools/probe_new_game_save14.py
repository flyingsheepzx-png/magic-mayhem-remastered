"""Owned save14 gameplay/reload reproduction with first-exception capture."""
import argparse,ctypes,time,os,threading,shutil,subprocess
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
import compare_remastered_ui_11 as c
from probe_11_close_wait import chains

def run(name,candidate=None,active=False,observe=True,intro=False):
 ctypes.windll.user32.SetProcessDPIAware()
 p=base.DEST;binary=candidate or c.ROOT/'modernization/build/remastered-1.1-reload-surface/candidate.exe'
 if candidate:
  assert all(resources(binary)[i]==resources(p/base.ENTRY)[i] for i in [101,103])
 else:assert resources(binary)==resources(p/base.ENTRY)
 identity=dict(version='1.1',package=str(p),launcher_name=base.ENTRY,launcher_sha256=c.sha(p/base.ENTRY),engine_sha256=c.ENGINES['1.1'])
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav')
 shutil.copy2(binary,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(binary)
 s=c.session_class()(identity,rt,out/'1.1',100)
 if intro:
  from ctypes import wintypes as W
  s.startup_fmv=True;seen={};skipped=[]
  s.u.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int]
  s.u.EnumChildWindows.argtypes=[W.HWND,s.cb,W.LPARAM]
  s.u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
  def skip_intro():
   def visit(h,unused):
    pid=W.DWORD();s.u.GetWindowThreadProcessId(h,ctypes.byref(pid))
    cls=ctypes.create_unicode_buffer(256);s.u.GetClassNameW(h,cls,256)
    if pid.value==s.pid and cls.value=='MagicMayhem.H264.FMV.v1':
     first=seen.setdefault(h,time.monotonic())
     if h not in skipped and time.monotonic()-first>.4:
      rect=W.RECT();assert s.u.GetClientRect(h,ctypes.byref(rect))
      lp=((rect.bottom//2)<<16)|(rect.right//2)
      assert s.u.PostMessageW(h,0x201,1,lp);assert s.u.PostMessageW(h,0x202,0,lp)
      skipped.append(h);c.write_json(out/'intro-skipped.json',dict(pid=s.pid,windows=skipped,class_name=cls.value))
    return True
   callback=s.cb(visit)
   def top(h,unused):
    pid=W.DWORD();s.u.GetWindowThreadProcessId(h,ctypes.byref(pid))
    if pid.value==s.pid:s.u.EnumChildWindows(h,callback,0)
    return True
   s.u.EnumWindows(s.cb(top),0)
  s.startup_ui_action=skip_intro
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
   phase[0]='new-game';s.click_base(640,396)
   deadline=time.monotonic()+8
   while time.monotonic()<deadline:
    if any(x['pointer']=='0x659d9d' or x['rect']==[1880,60,2024,204] for x in s.controls()):break
    time.sleep(.025)
   else:raise RuntimeError('New game page not ready')
   c.write_json(out/'new-game-controls.json',s.controls())
   phase[0]='escape-new-game';s.key(0x1b);time.sleep(.15)
   deadline=time.monotonic()+5
   while time.monotonic()<deadline:
    if any(x['rect']==[680,864,1880,960] for x in s.controls()):break
    time.sleep(.025)
   else:raise RuntimeError('Main menu not restored by Esc')
   c.write_json(out/'returned-controls.json',s.controls())
   load('14','main')
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
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--candidate',type=Path);p.add_argument('--active-actions',action='store_true');p.add_argument('--no-observer',action='store_true');p.add_argument('--intro',action='store_true');a=p.parse_args();run(a.name,a.candidate,a.active_actions,not a.no_observer,a.intro)
