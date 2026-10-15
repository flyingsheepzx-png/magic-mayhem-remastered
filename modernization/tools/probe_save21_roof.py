"""Authorized isolated save21 roof reproduction, private input/read-only state."""
import argparse,time,struct,shutil,re
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read
def run(name,candidate=None):
 base.idle();out=c.ROOT/'modernization/logs/remastered-ui'/('save21-roof-'+name);out.mkdir(exist_ok=False)
 fixture=base.DEST/'runtime/Save/21.sav';formal=base.DEST/base.ENTRY
 binary=candidate or c.ROOT/'modernization/playtests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe'
 if candidate is None:assert resources(binary)==resources(formal)
 identity=dict(version='1.1',package=str(base.DEST),launcher_name=base.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture);shutil.copy2(binary,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(binary)
 prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
 build=candidate.parent if candidate else c.ROOT/'modernization/build/remastered-1.1-roof-ghost'
 lines=(build/'repath.map').read_text().splitlines()
 def sym(name):return int(next(x for x in lines if '?'+name+'@@' in x).split()[2],16)
 s=c.session_class()(identity,rt,out/'run',65);samples=[]
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666);deadline=time.monotonic()+12
  while time.monotonic()<deadline:
   u=s.i(0x6def58)
   if u and s.i(u+4) and s.i(0x6df180)>0:break
   time.sleep(.1)
  assert u and s.i(u+4);time.sleep(.6)
  code=read(s.k,s.handle,0x4fd552,5);delta=0x4fd557+struct.unpack('<i',code[1:])[0]-sym('before_hook')
  deadline=time.monotonic()+8
  while time.monotonic()<deadline:
   if read(s.k,s.handle,sym('captured')+delta,1)==b'\1':break
   time.sleep(.1)
  assert read(s.k,s.handle,sym('captured')+delta,1)==b'\1'
  def capture(label):
   blob=read(s.k,s.handle,u,0xe4b);(out/(label+'-unit.bin')).write_bytes(blob)
   fields={hex(o):struct.unpack_from('<i',blob,o)[0] for o in [4,8,12,16,0x14,0x18,0x1c,0x24,0x28,0x2c,0xe4,0xb4,0xcc,0xac,0x855,0x829,0x841,0xcf7,0xbf3,0xcfb]}
   telemetry={n:s.i(sym(n)+delta) for n in ['roof_count','command_count','frame_width','frame_height']}
   gates={n:list(read(s.k,s.handle,sym(n)+delta,1)) for n in ['captured','replay_enabled','occluded_units_enabled']}
   scene={hex(o):s.i(0x689930+o) for o in [0x31,0x39,0x3d,0x5d,0x61,0x65,0x6d,0x79]}
   row=dict(label=label,unit=fields,telemetry=telemetry,gates=gates,scene=scene,roof=[s.i(a) for a in [0x689995,0x689999,0x68999d]],player=s.i(0x644520))
   for off,size in [(0xb4,16),(0xcc,0x114),(0xcf7,720),(0xac,20)]:
    ptr=fields[hex(off)]
    if ptr:(out/(label+'-'+hex(off)+'.bin')).write_bytes(read(s.k,s.handle,ptr,size))
   if telemetry['roof_count']>0:
    row['ghosts']=list(struct.unpack('<9i',read(s.k,s.handle,sym('roof_bodies')+delta,36)))
   samples.append(row);print(row,flush=True);c.write_json(out/'telemetry.json',samples);s.shot(label,False)
   if telemetry['roof_count']>0:
    (out/(label+'-unoccluded.bin')).write_bytes(read(s.k,s.handle,sym('unoccluded')+delta,1280*720*2))
  capture('loaded')
  for i in range(2):s.key(9);time.sleep(.4);capture('tab'+str(i+1))
  c.write_json(out/'records.json',s.records)
 assert s.result['restored'] and not s.result['cleanup_errors'];print(out)
if __name__=='__main__':
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--candidate',type=Path);a=p.parse_args();run(a.name,a.candidate)
