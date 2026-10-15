"""Owned isolated save22 terrain capture; private input and read-only telemetry."""
import argparse,time,struct,json,shutil
from pathlib import Path
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as b
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read
from spr_assets import read_spr
def run(name,replacement=None):
 b.idle();out=c.ROOT/'modernization/logs/terrain-hd'/name;out.mkdir(parents=True,exist_ok=False)
 formal=b.DEST/b.ENTRY;fixture=b.DEST/'runtime/Save/22.sav'
 manifest=json.loads((b.DEST/'release-manifest.json').read_text(encoding='utf-8'))
 assert c.sha(formal)==manifest['launcher_sha256'] and c.sha(b.DEST/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']==c.ENGINES['1.1']
 identity=dict(version='1.1',package=str(b.DEST),launcher_name=b.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=manifest['engine_sha256'])
 rt=c.stage(identity,out/'package',fixture)
 # Formal player launcher sanitizes diagnostic variables; use hash-verified
 # development launcher with identical embedded modules in this disposable lab.
 candidate=c.ROOT/'modernization/playtests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe'
 cm=json.loads((candidate.parent/'manifest.json').read_text(encoding='utf-8'))
 assert c.sha(candidate)==cm['launcher_sha256'] and resources(candidate)==resources(formal)
 shutil.copy2(candidate,rt.parent/b.ENTRY);identity['launcher_sha256']=c.sha(candidate)
 if replacement:
  v=json.loads((replacement.parent/'verification.json').read_text(encoding='utf-8'));assert c.sha(replacement)==v['candidate_sha256']
  for rel in [v['runtime_path'],v['equivalent_runtime_path']]:
   dest=rt/rel;assert c.sha(dest)==v['original_sha256'];shutil.copy2(replacement,dest)
 s=c.session_class()(identity,rt,out/'run',65)
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666);deadline=time.monotonic()+12
  while time.monotonic()<deadline:
   unit=s.i(0x6def58)
   if unit and s.i(unit+4) and s.i(0x6df180)>0:break
   time.sleep(.1)
  assert unit and s.i(unit+4) and s.i(0x6df180)>0,'No live unit after loading';time.sleep(.7)
  unit=s.i(0x6def58);dims=[s.i(a) for a in (0x6c5494,0x6c5498,0x6c549c)]
  scene=read(s.k,s.handle,0x689930,0x240);(out/'scene.bin').write_bytes(scene)
  manager=s.i(0x689930+0x2d);ptr,unknown,offsets,start=struct.unpack('<4I',read(s.k,s.handle,manager,16));headers=[]
  for index in [0,1,2,10,100,666,699,721,727,728,733]:
   sprite=s.i(offsets+index*4)+start;header=read(s.k,s.handle,sprite,40);palette=struct.unpack_from('<I',header,28)[0]
   palette_raw=read(s.k,s.handle,palette,512) if palette and palette!=0xffffffff else b''
   if palette_raw:(out/f'palette-{index}.bin').write_bytes(palette_raw)
   if palette_raw:
    colour_pointer=struct.unpack_from('<I',palette_raw,0)[0]
    if colour_pointer:(out/f'palette-colours-{index}.bin').write_bytes(read(s.k,s.handle,colour_pointer,512))
   headers.append({'index':index,'header':header.hex(),'palette_rgb565_sha256':__import__('hashlib').sha256(palette_raw).hexdigest() if palette_raw else None})
  matches=[]
  for file in rt.glob('Realms/**/Terrain.spr'):
   palettes,frames=read_spr(file)
   matched=[r['index'] for r in headers if r['index']<len(frames) and frames[r['index']]['data'][:28].hex()==r['header'][:56]]
   if matched:matches.append({'path':file.relative_to(rt).as_posix(),'sha256':c.sha(file),'frames':len(frames),'palettes':len(palettes),'matched_indices':matched,'palette_hashes':[__import__('hashlib').sha256(p).hexdigest() for p in palettes]})
  s.message(0x200,2560-20,1440-20);time.sleep(.2);s.shot('battle',False)
  c.write_json(out/'capture.json',{'fixture_sha256':c.sha(fixture),'mode':s.i(0x6903e8),'dimensions':dims,'hero':[s.i(unit+a) for a in [8,12,16]],'terrain_matches':matches,'headers':headers,'identity':identity,'replacement':str(replacement) if replacement else None})
 assert s.result['restored'] and not s.result['cleanup_errors'];print(out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--replacement',type=Path);a=p.parse_args();run(a.name,a.replacement)
