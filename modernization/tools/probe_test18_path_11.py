"""User-authorized test18 replay, background input and read-only route telemetry."""
import argparse,ctypes,time,os,struct
import compare_remastered_ui_11 as c
from verify_hd60_runtime import read
def run(name):
 ctypes.windll.user32.SetProcessDPIAware()
 p=c.CANDIDATE;f=p/'runtime/Save/test18.sav';identity=c.verify_package(p,'1.1',c.sha(p/'manifest.json'))
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 s=c.session_class()(identity,p/'runtime',out/'1.1',100)
 samples=[]
 with s:
  stamp=time.time_ns();os.utime(s.lab/'Save'/f.name,ns=(stamp,stamp))
  s.click_base(640,456);time.sleep(.7)
  rect=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8')
  height=s.i(s.i(0x656680)+16)+2;x=(rect[0]+rect[2])//2;y=int(rect[1]+height/2)
  for event in [0x200,0x201,0x202]:s.message(event,x,y);time.sleep(.09)
  s.click_base(328,666)
  start=time.monotonic();captured=False;roof=False;last=None
  while time.monotonic()-start<14:
   count=s.i(0x6df180);base=s.i(0x6def58);cap=s.i(0x6def5c)
   if base and 0<count<=cap<=1024:
    blob=read(s.k,s.handle,base,0xe4b);v=lambda off:struct.unpack_from('<i',blob,off)[0]
    dims=[s.i(a) for a in [0x6c5494,0x6c5498,0x6c549c]]
    if v(4) and all(0<=v(o)<d for o,d in zip([8,12,16],dims)):
     state=dict(grid=[v(o) for o in [8,12,16]],world=[v(o) for o in [0x14,0x18,0x1c]],order=v(0x5ec),action=v(0x5fc),motion=v(0x618),macro=v(0xd03),route=list(struct.unpack_from('<131i',blob,0x96b)),kind=v(0x10c),selected=v(0x68))
     if state!=last:samples.append(dict(seconds=time.monotonic()-start,**state));last=state
     if not captured:
      (out/'unit0.bin').write_bytes(blob);cells=s.i(0x6c54dc);assert 0<dims[0]*dims[1]*dims[2]<=4000000
      raw=read(s.k,s.handle,cells,12*dims[0]*dims[1]*dims[2]);(out/'map.bin').write_bytes(raw)
      tilecount=max(struct.unpack_from('<H',raw,j)[0] for j in range(0,len(raw),12))+1;assert tilecount<4096
      (out/'tile-types.bin').write_bytes(read(s.k,s.handle,s.i(0x65660c),tilecount*0x164));(out/'unit-type.bin').write_bytes(read(s.k,s.handle,v(0xac),0x100))
      c.write_json(out/'capture.json',dict(dimensions=dims,fixture_sha256=c.sha(f),unit_address=base,identity=identity));captured=True
      print('initial',state['grid'],'goal',state['route'][:3],'route',state['route'][3:5],flush=True)
     if not roof:
      # Native portrait rectangle, logical battle coordinates. Double click.
      controls=s.controls();c.write_json(out/'controls.json',controls)
      for _ in range(2):
       for ev in [0x200,0x201,0x202]:s.message(ev,1217*2,640*2);time.sleep(.045)
      roof=True;s.shot('roof-toggled',False)
   time.sleep(.02)
  assert captured and samples
  s.shot('route-end',False)
  c.write_json(out/'samples.json',samples)
 c.write_json(out/'probe.json',dict(result=s.result,screens=s.records,fixture_sha256=c.sha(f),sample_count=len(samples)))
 print(out,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);run(p.parse_args().name)
