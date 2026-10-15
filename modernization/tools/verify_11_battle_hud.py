"""Compile/run actual output HUD code against production pack and saved pixels."""
import json,struct,shutil,subprocess
import numpy as np
from PIL import Image
import build_remastered_11 as b
from build_11_battle_hud import OUT,ASSET

def verify():
 ws=OUT/'wrapper';old=b.ROOT/'modernization/build/remastered-1.1-portable-render/wrapper/src/mm_mixed.h'
 s=(ws/'src/mm_mixed.h').read_text()
 assert s.replace('#include "mm_battle_hud.h"\n\n','').replace('    mm_hud_present(primary,mm_mixed_pixels);\n','')==old.read_text()
 for p in [b.SRC/'hud_overlay_core.h',b.ROOT/'modernization/wrapper-probe/mm_battle_hud.h']:
  assert p.read_bytes()==(ws/'src'/p.name).read_bytes();shutil.copy2(p,OUT/p.name)
 for p in [b.SRC/'layout_context.h',b.ROOT/'modernization/tests/battle_hud_overlay_test.cpp']:shutil.copy2(p,OUT/p.name)
 runtime=OUT/'test-runtime';(runtime/'Sprites').mkdir(parents=True,exist_ok=True)
 shutil.copy2(ASSET/'battle-hud.bin',runtime/'Sprites/battle-hud.bin')
 capture=b.ROOT/'modernization/logs/remastered-ui/save10-minimap-fixed-20261001/run/capture.json'
 record=json.loads(capture.read_text())['screens']['battle-save10']
 assert b.sha(b.Path(record['output']))==record['sha256']
 rgb=np.asarray(Image.open(record['native']).convert('RGB'),dtype=np.uint16)[::2,::2]
 low=((rgb[:,:,0]>>3)<<11)|((rgb[:,:,1]>>2)<<5)|(rgb[:,:,2]>>3)
 surface=np.zeros((1440,2560),dtype='<u2');surface[:720,:1280]=low
 (runtime/'scene.bin').write_bytes(surface.tobytes())
 controls=record['controls']
 (runtime/'controls.bin').write_bytes(struct.pack('<I',len(controls))+b''.join(struct.pack('<5I',int(c['vtable'],16),*c['rect']) for c in controls))
 (OUT/'test.cmd').write_text('@echo off\ncall "'+str(b.VC)+'" x86 >nul\nif errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 battle_hud_overlay_test.cpp /link /OUT:battle_hud_overlay_test.exe\n')
 pack=json.loads((ASSET/'pack.json').read_text());assert pack['portraits_complete']
 entries=pack['entries'];lookup={e['name']:i for i,e in enumerate(entries)};pairs=[]
 for name,index in lookup.items():
  if ':0:face-core' in name:pairs.append((index,lookup[name.replace(':0:face-core',':1:face-core')]))
 (runtime/'healthpairs.bin').write_bytes(struct.pack('<I',len(pairs))+b''.join(struct.pack('<2I',*p) for p in pairs))
 subprocess.run(['cmd','/c','test.cmd'],cwd=OUT,check=True)
 outputs=[]
 for args in [[],['captured']]:
  r=subprocess.run([str(OUT/'battle_hud_overlay_test.exe'),*args],cwd=runtime,check=True,capture_output=True,text=True);print(r.stdout);outputs.append(r.stdout)
 v=dict(result='passed',native_tests=outputs,pack_sha256=b.sha(ASSET/'battle-hud.bin'),wrapper_sha256=b.sha(ws/'bin/Release/ddraw.dll'),
        native_battle=[1280,720],output=[2560,1440],input_unchanged=True,primary_unchanged=True,
        source_delta='HUD include/call only; original mode/input/scale/identity logic byte-equivalent',
        runtime_acceptance='pending user acceptance; see runtime-verification.json for authorized isolated save10 checks',
        fallback='original native pixels for unsupported/occluded frames; negative cache up to500ms unless frame/state/rect changes')
 b.write(OUT/'verification.json',v)
 return v

if __name__=='__main__':verify()
