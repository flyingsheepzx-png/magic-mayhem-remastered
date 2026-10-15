"""Authorized save13 routing capture, private input and read-only telemetry."""
import argparse,time,struct,shutil
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read

def run(name,candidate=None):
 base.idle()
 out=c.ROOT/'modernization/logs/remastered-ui'/('save17-route-'+name);out.mkdir(exist_ok=False)
 fixture=base.DEST/'runtime/Save/17.sav'
 formal=base.DEST/base.ENTRY
 binary=candidate or c.ROOT/'modernization/playtests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe'
 if not candidate:assert resources(binary)==resources(formal)
 identity=dict(version='1.1',package=str(base.DEST),launcher_name=base.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture)
 shutil.copy2(binary,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(binary)
 if candidate and (candidate.parent/'terrain_diagonal.dll').exists():shutil.copy2(candidate.parent/'terrain_diagonal.dll',rt/'terrain_diagonal.dll')
 prefs=rt/'CFG/prefs.cfg';import re;prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
 s=c.session_class()(identity,rt,out/'run',230);samples=[]
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666);start=time.monotonic();captured=False;last=None
  while time.monotonic()-start<190:
   address=s.i(0x6def58);count=s.i(0x6df180);capacity=s.i(0x6def5c)
   if address and 0<count<=capacity<=1024:
    blob=read(s.k,s.handle,address,0xe4b);v=lambda o:struct.unpack_from('<i',blob,o)[0]
    dims=[s.i(a) for a in (0x6c5494,0x6c5498,0x6c549c)]
    if v(4) and all(0<=v(o)<b for o,b in zip((8,12,16),dims)):
     state=dict(grid=[v(o) for o in (8,12,16)],world=[v(o) for o in (0x14,0x18,0x1c)],order=v(0x5ec),action=v(0x5fc),motion=v(0x618),macro=v(0xd03),route=list(struct.unpack_from('<131i',blob,0x96b)),kind=v(0x10c))
     if state!=last:samples.append(dict(seconds=time.monotonic()-start,**state));last=state
     if int(time.monotonic()-start)//15>int(samples[0].get('progress',-1)):
      samples[0]['progress']=int(time.monotonic()-start)//15;print('progress',round(time.monotonic()-start,1),state['grid'],state['route'][:5],flush=True)
     if state['grid']==[71,71,8]:break
     if not captured:
      (out/'unit0.bin').write_bytes(blob);raw=read(s.k,s.handle,s.i(0x6c54dc),12*dims[0]*dims[1]*dims[2]);(out/'map.bin').write_bytes(raw)
      n=max(struct.unpack_from('<H',raw,j)[0] for j in range(0,len(raw),12))+1;assert n<4096
      (out/'tile-types.bin').write_bytes(read(s.k,s.handle,s.i(0x65660c),n*0x164))
      (out/'unit-type.bin').write_bytes(read(s.k,s.handle,v(0xac),0x100))
      c.write_json(out/'capture.json',dict(dimensions=dims,fixture_sha256=c.sha(fixture),unit_address=address,identity=identity))
      print('initial',state['grid'],'goal',state['route'][:3],'route',state['route'][3:5],flush=True);captured=True
   time.sleep(.025)
  assert captured;c.write_json(out/'samples.json',samples);s.shot('route-end',False);c.write_json(out/'samples.json',samples)
 assert s.result['restored'] and not s.result['cleanup_errors']
 print(out)

if __name__=='__main__':
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--candidate',type=Path);a=p.parse_args();run(a.name,a.candidate)
