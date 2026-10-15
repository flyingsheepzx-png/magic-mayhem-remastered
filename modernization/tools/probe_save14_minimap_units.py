"""Authorized save14 scanner capture; read-only unit/scanner state."""
import time,struct,shutil,argparse
from pathlib import Path
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as life
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read

def run(name,candidate=None):
 life.idle();out=c.ROOT/'modernization/logs/remastered-ui'/('save14-minimap-units-'+name);out.mkdir(exist_ok=False)
 formal=life.DEST/life.ENTRY;fixture=life.DEST/'runtime/Save/14.sav'
 identity=dict(version='1.1',package=str(life.DEST),launcher_name=life.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture);binary=candidate or c.ROOT/'modernization/build/remastered-1.1-half-stair/candidate.exe'
 if not candidate:assert resources(binary)==resources(formal)
 shutil.copy2(binary,rt.parent/life.ENTRY);identity['launcher_sha256']=c.sha(binary)
 s=c.session_class()(identity,rt,out/'run',80)
 with s:
  s.load_fixture('14');c.wait_control(s,lambda r:r['vtable']=='0x5c6f54');time.sleep(.5)
  scanner=c.wait_control(s,lambda r:r['vtable']=='0x5c6a8c');assert len(scanner)==1
  obj=int(scanner[0]['pointer'],16);blob=read(s.k,s.handle,obj,0x6700);(out/'scanner.bin').write_bytes(blob)
  start=s.i(0x6def58);capacity=s.i(0x6def5c);assert 0<capacity<=1024
  (out/'units.bin').write_bytes(read(s.k,s.handle,start,capacity*0xe4b))
  c.write_json(out/'state.json',dict(scanner=scanner[0],unit_start=start,capacity=capacity,dimensions=[s.i(a) for a in [0x6c5494,0x6c5498,0x6c549c]],scanner_words={hex(o):struct.unpack_from('<i',blob,o)[0] for o in [0xbe,0xca,0xd6,0xda,0xeb,0x6199,0x619d,0x65af,0x65b3]},engine_sha256=identity['engine_sha256']))
  s.shot('battle',False);s.key(0x20);time.sleep(.2);s.shot('battle-paused',False)
 assert s.result['restored'] and not s.result['cleanup_errors'];print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--candidate',type=Path);a=p.parse_args();run(a.name,a.candidate)
