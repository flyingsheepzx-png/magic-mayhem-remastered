"""Save24 canopy picking reproduction in isolated runtime, read-only telemetry."""
import argparse,time,struct,shutil,re
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read
def run(name,candidate=None,click=False,click_x=672,click_y=344):
 base.idle();out=c.ROOT/'modernization/logs/remastered-ui'/('save24-pick-'+name);out.mkdir(exist_ok=False)
 fixture=base.DEST/'runtime/Save/24.sav';formal=base.DEST/base.ENTRY
 binary=candidate or c.ROOT/'modernization/playtests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe'
 if candidate is None:assert resources(binary)==resources(formal)
 identity=dict(version='1.1',package=str(base.DEST),launcher_name=base.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture);shutil.copy2(binary,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(binary)
 prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
 s=c.session_class()(identity,rt,out/'run',70)
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666);time.sleep(2.5)
  unit=s.i(0x6def58);blob=read(s.k,s.handle,unit,0xe4b);(out/'unit0.bin').write_bytes(blob)
  dims=[s.i(a) for a in (0x6c5494,0x6c5498,0x6c549c)];raw=read(s.k,s.handle,s.i(0x6c54dc),12*dims[0]*dims[1]*dims[2]);(out/'map.bin').write_bytes(raw)
  n=max(struct.unpack_from('<H',raw,j)[0] for j in range(0,len(raw),12))+1;assert n<4096
  (out/'tile-types.bin').write_bytes(read(s.k,s.handle,s.i(0x65660c),n*0x164))
  (out/'scene.bin').write_bytes(read(s.k,s.handle,0x689930,0x240))
  manager=s.i(0x689930+0x2d); table=read(s.k,s.handle,manager,16); ptr,unknown,offsets,start=struct.unpack('<4I',table)
  headers=[]
  for index in (666,699,721,727,728,733):
   sprite=s.i(offsets+index*4)+start
   headers.append(dict(index=index,pointer=sprite,header=read(s.k,s.handle,sprite,40).hex()))
  c.write_json(out/'sprite-headers.json',headers)
  c.write_json(out/'capture.json',dict(mode=s.i(0x6903e8),dimensions=dims,hero=list(struct.unpack_from('<3i',blob,8)),fixture_sha256=c.sha(fixture),identity=identity))
  s.shot('loaded',False);rows=[]
  symbols=None
  if click:
   call=read(s.k,s.handle,0x4f8aee,5);assert call[0]==0xe8
   target=0x4f8aee+5+struct.unpack_from('<i',call,1)[0]
   lines=(candidate.parent/'qol_bindings.map').read_text().splitlines()
   def sym(n):return int(next(x for x in lines if '?'+n+'@' in x).split()[2],16)
   delta=target-sym('canopy_mask');symbols=(sym,delta)
  for y in range(280,425,16):
   for x in range(560,705,16):
    s.message(0x200,x*2,y*2);time.sleep(.045)
    row=dict(mouse=[x,y],terrain=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)],unit=s.i(0x656600),kind=s.i(0x6a5134),cursor=s.i(0x5e04c8))
    if symbols:
     n=s.i(sym('pick_count')+delta);assert 0<=n<=128
     row['cells']=list(struct.iter_unpack('<3i',read(s.k,s.handle,sym('pick_cells')+delta,n*12))) if n else []
    rows.append(row)
  c.write_json(out/'hover.json',rows);s.shot('hover-end',False);c.write_json(out/'records.json',s.records)
  if click:
   if not s.i(unit+0x68):s.click_base(648,330);time.sleep(.2)
   selection=[i for i in range(s.i(0x6def5c)) if s.i(s.i(0x6def58)+i*0xe4b+0x68)]
   c.write_json(out/'selection.json',selection);assert 0 in selection
   s.message(0x200,click_x*2,click_y*2);time.sleep(.2)
   # The mask adapter's resolved CALL yields module base without OS module APIs.
   address=0x4f8aee;call=read(s.k,s.handle,address,5);assert call[0]==0xe8
   target=address+5+struct.unpack_from('<i',call,1)[0]
   lines=(candidate.parent/'qol_bindings.map').read_text().splitlines()
   def sym(n):return int(next(x for x in lines if '?'+n+'@' in x).split()[2],16)
   delta=target-sym('canopy_mask')
   def snap():
    count=s.i(sym('pick_count')+delta);assert 0<=count<=128
    cells=list(struct.iter_unpack('<3i',read(s.k,s.handle,sym('pick_cells')+delta,count*12))) if count else []
    surfaces=s.i(sym('pick_surface_count')+delta);assert 0<=surfaces<=128
    footprint=list(struct.iter_unpack('<3i',read(s.k,s.handle,sym('pick_surfaces')+delta,surfaces*12))) if surfaces else []
    return dict(footprint=footprint,terrain=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)],kind=s.i(0x6a5134),mode=s.i(0x6903e8),cells=cells,status=s.i(sym('pick_last_status')+delta),raw=list(struct.unpack('<3i',read(s.k,s.handle,sym('pick_last_raw')+delta,12))),replacement=list(struct.unpack('<3i',read(s.k,s.handle,sym('pick_last_replacement')+delta,12))),hero=[s.i(unit+a) for a in (8,12,16)],goal=[s.i(unit+a) for a in (0x96b,0x96f,0x973)])
   before=snap();s.message(0x204,click_x*2,click_y*2);time.sleep(.09);after=snap();s.message(0x205,click_x*2,click_y*2)
   c.write_json(out/'click.json',dict(before=before,after=after));time.sleep(.3)
 assert s.result['restored'] and not s.result['cleanup_errors'];print(out)
if __name__=='__main__':
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--candidate',type=Path);p.add_argument('--click',action='store_true');p.add_argument('--click-x',type=int,default=684);p.add_argument('--click-y',type=int,default=338);a=p.parse_args();run(a.name,a.candidate,a.click,a.click_x,a.click_y)
