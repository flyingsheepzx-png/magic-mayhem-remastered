"""Authorized save3 read-only route and terrain capture in an isolated copy."""
import time,struct,argparse
import debug_11_portable_save1 as d
import build_11_character_icons as icons
import compare_remastered_ui_11 as c
from verify_hd60_runtime import read
def run(name):
 d.FIXTURE=d.lifecycle.DEST/'runtime/Save/3.sav'
 # Latest diagnostic launcher retains exact formal module resources.
 d.lifecycle.OUT=icons.OUT
 rt,identity=d.staged('route3-'+name,d.lifecycle.DEST/'runtime/ddraw.dll')
 if name.startswith('after'):
  import shutil
  source=c.ROOT/'modernization/build/remastered-1.1-local-route/candidate.exe'
  shutil.copy2(source,rt.parent/identity['launcher_name']);identity['launcher_sha256']=c.sha(source)
 out=c.ROOT/'modernization/logs/remastered-ui'/('save3-route-'+name);out.mkdir(exist_ok=False)
 s=c.session_class()(identity,rt,out/'capture',80);samples=[]
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666);start=time.monotonic();captured=False;last=None
  while time.monotonic()-start<18:
   base=s.i(0x6def58);count=s.i(0x6df180);capacity=s.i(0x6def5c)
   if base and 0<count<=capacity<=1024:
    blob=read(s.k,s.handle,base,0xe4b);v=lambda o:struct.unpack_from('<i',blob,o)[0]
    dims=[s.i(a) for a in (0x6c5494,0x6c5498,0x6c549c)]
    if v(4) and all(0<=v(o)<b for o,b in zip((8,12,16),dims)):
     state=dict(grid=[v(o) for o in (8,12,16)],world=[v(o) for o in (0x14,0x18,0x1c)],order=v(0x5ec),action=v(0x5fc),motion=v(0x618),macro=v(0xd03),route=list(struct.unpack_from('<131i',blob,0x96b)),kind=v(0x10c))
     if state!=last:samples.append(dict(seconds=time.monotonic()-start,**state));last=state
     if not captured:
      (out/'unit0.bin').write_bytes(blob);cells=s.i(0x6c54dc);assert 0<dims[0]*dims[1]*dims[2]<4000000
      raw=read(s.k,s.handle,cells,12*dims[0]*dims[1]*dims[2]);(out/'map.bin').write_bytes(raw)
      n=max(struct.unpack_from('<H',raw,j)[0] for j in range(0,len(raw),12))+1;assert n<4096
      (out/'tile-types.bin').write_bytes(read(s.k,s.handle,s.i(0x65660c),n*0x164))
      (out/'unit-type.bin').write_bytes(read(s.k,s.handle,v(0xac),0x100))
      c.write_json(out/'capture.json',dict(dimensions=dims,fixture_sha256=c.sha(d.FIXTURE),unit_address=base,identity=identity))
      print('initial',state['grid'],'goal',state['route'][:3],'route',state['route'][3:5],flush=True);captured=True
   time.sleep(.025)
  assert captured;s.shot('route-end');c.write_json(out/'samples.json',samples)
 print(out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');run(p.parse_args().name)
