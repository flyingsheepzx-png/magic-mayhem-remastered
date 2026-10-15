"""Isolated save18 group-order reproduction using private input/read-only memory."""
import argparse,json,re,shutil,struct,time,threading
from pathlib import Path
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read

def run(name):
 base.idle()
 out=c.ROOT/'modernization/logs/remastered-ui'/('save18-command-'+name);out.mkdir(exist_ok=False)
 formal=base.DEST/base.ENTRY;candidate=base.b.TARGET/'MagicMayhem-Remastered-1.1.exe'
 manifest=json.loads((base.DEST/'release-manifest.json').read_text(encoding='utf-8'))
 assert c.sha(formal)==manifest['launcher_sha256'] and resources(candidate)==resources(formal)
 identity=dict(version='1.1',package=str(base.DEST),launcher_name=base.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 fixture=base.DEST/'runtime/Save/18.sav';rt=c.stage(identity,out/'package',fixture)
 shutil.copy2(candidate,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
 prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
 s=c.session_class()(identity,rt,out/'run',180);samples=[];events=[];stop=threading.Event()
 def snapshot():
  pool=s.i(0x6def58);cap=s.i(0x6def5c);assert pool and 0<cap<=1024
  data=read(s.k,s.handle,pool,cap*0xe4b);units=[]
  for index in range(cap):
   b=data[index*0xe4b:(index+1)*0xe4b];v=lambda o:struct.unpack_from('<i',b,o)[0]
   if not v(4):continue
   units.append(dict(index=index,id=v(0),owner=v(0x174),type=v(0xa8),selected=v(0x68),health=v(0xe4),grid=[v(i) for i in (8,12,16)],world=[v(i) for i in (20,24,28)],state=v(0x5ec),pending=v(0x5f0),command=v(0x5fc),motion=v(0x618),target=v(0x64c),attached=v(0x664),wait=v(0x66c),route=list(struct.unpack_from('<5i',b,0x96b))))
  return dict(seconds=time.perf_counter()-start,game_time=s.i(0x6c4830),units=units)
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666)
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   if s.i(0x6def58) and s.i(0x6df180)>0 and any(x['vtable']=='0x5c6f54' for x in s.controls()):break
   time.sleep(.05)
  else:raise RuntimeError('save18 did not enter battle')
  start=time.perf_counter();initial=snapshot();c.write_json(out/'initial.json',initial)
  s.shot('initial',False);print('READY',out,flush=True)
  def collect():
   last=None
   try:
    while not stop.is_set():
     snap=snapshot()
     signature=[(u['index'],u['selected'],u['state'],u['pending'],u['command'],u['motion'],u['target'],u['grid'],u['route']) for u in snap['units']]
     if signature!=last:samples.append(snap);last=signature
     time.sleep(.003)
   except BaseException as e:events.append(dict(error=str(e)))
  collector=threading.Thread(target=collect);collector.start()
  try:
   action=out/'actions.json';deadline=time.monotonic()+110
   while not action.exists() and time.monotonic()<deadline:time.sleep(.1)
   assert action.exists(),'No private-input actions supplied'
   for a in json.loads(action.read_text()):
    events.append(dict(seconds=time.perf_counter()-start,action=a))
    if a['kind']=='drag':
     x,y=a['from'];tx,ty=a['to'];s.message(0x200,x,y);s.message(0x201,x,y);time.sleep(.1)
     for i in range(1,11):s.message(0x200,x+(tx-x)*i//10,y+(ty-y)*i//10);time.sleep(.03)
     s.message(0x202,tx,ty);time.sleep(.12)
     c.write_json(out/'selected.json',snapshot())
    elif a['kind']=='click':
     x,y=a['point'];s.message(0x200,x,y);time.sleep(.04)
     s.message(0x204 if a.get('right') else 0x201,x,y);time.sleep(.09)
     s.message(0x205 if a.get('right') else 0x202,x,y)
    elif a['kind']=='wait':time.sleep(a['seconds'])
    elif a['kind']=='shot':s.shot(a['name'],False)
   time.sleep(2);s.shot('end',False)
  finally:
   stop.set();collector.join(5);c.write_json(out/'samples.json',samples);c.write_json(out/'events.json',events)
   c.write_json(out/'identity.json',dict(**identity,fixture_sha256=c.sha(fixture)))
 assert s.result['restored'] and not s.result['cleanup_errors']
 print('DONE',len(samples),out,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');run(p.parse_args().name)
