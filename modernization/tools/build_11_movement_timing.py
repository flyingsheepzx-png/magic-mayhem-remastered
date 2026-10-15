"""Iteration1 only: exact logic cadence, shared read-only render prediction."""
import argparse,json,shutil,subprocess
import build_11_roof_click_floor as prev
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-movement-timing'
BACK=b.ROOT/'modernization/backups/remastered-1.1-movement-timing'
SOURCE=b.ROOT/'modernization/build/remastered-1.1-roof-ghost-v2'
LATEST=prev.OUT

def build():
 current=resources(base.DEST/base.ENTRY)
 assert current==resources(LATEST/'release.exe')
 assert current[101]==(SOURCE/'repath.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  j=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==j['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==j['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.dll'):shutil.copy2(p,OUT/p.name)
 for name in ['launcher.cpp','release_launcher.cpp']:shutil.copy2(LATEST/name,OUT/name)
 for i,name in [(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'movement_timing.h',OUT/'movement_timing.h')
 p=OUT/'logic_time_trial.cpp';s=p.read_text()
 s=b.replace_once(s,'#include <string.h>','#include <string.h>\n#include "movement_timing.h"')
 start=s.index('    if (*(int*)0x6de6fd!=30');end=s.index('\n}',start)
 s=s[:start]+'''    unsigned id=*(unsigned short*)unit;
    int rate=*(int*)0x6de6fd,players=*(int*)0x6e1f0c;
    if(!mm_movement::compensated(original,rate,players,id))return original;
    Phase& phase=phases[id];
    if(phase.unit!=unit){phase.unit=unit;phase.remainder=0;}
    auto next=mm_movement::contribution(original,phase.remainder,rate,players,id,original_walltime_trial);
    phase.remainder=next.remainder;return next.amount;
''' +s[end:]
 anchor='__declspec(naked) static void speed_hook()'
 s=b.replace_once(s,anchor,'''extern "C" int __cdecl mm_movement_prediction_contribution(void* unit){
    int speed=*(int*)((char*)unit+0xb63);
    unsigned id=*(unsigned short*)unit;
    int rate=*(int*)0x6de6fd,players=*(int*)0x6e1f0c;
    if(!mm_movement::compensated(speed,rate,players,id))return speed;
    // Snapshot the NEXT integer contribution, including the current fractional
    // carry. Never consume/reset logic carry or alter unit motion state here.
    const Phase& phase=phases[id];
    int remainder=phase.unit==unit?phase.remainder:0;
    return mm_movement::contribution(speed,remainder,rate,players,id,original_walltime_trial).amount;
}
''' +anchor)
 p.write_text(s)
 p=OUT/'render_replay_trial.cpp';s=p.read_text()
 s=b.replace_once(s,'#include "ui_layout.h"','#include "ui_layout.h"\n#include "movement_timing.h"\nextern "C" int __cdecl mm_movement_prediction_contribution(void*);')
 s=b.replace_once(s,'a.speed=(double)f(unit,0xb63)/threshold;','a.speed=(double)mm_movement_prediction_contribution(unit)/threshold;')
 s=b.replace_once(s,'double fraction=elapsed/span;if(fraction>0.75)fraction=0.75;','double fraction=mm_movement::replay_ticks(elapsed,span,g(0x6de6fd),continuous_enabled);')
 p.write_text(s)
 base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()

def verify():
 current=resources(LATEST/'release.exe')
 for n in ['candidate.exe','release.exe']:
  r=resources(OUT/n);assert set(r)==set(current)
  assert all(r[i]==((OUT/'repath.dll').read_bytes() if i==101 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name not in ('logic_time_trial.cpp','render_replay_trial.cpp','launcher.cpp','release_launcher.cpp'):
   assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
 for n in ['launcher.cpp','release_launcher.cpp']:assert (OUT/n).read_bytes()==(LATEST/n).read_bytes()

def install():
 verify();v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'repath.dll')
 assert (OUT/'movement_timing.h').read_bytes()==(b.SRC/'movement_timing.h').read_bytes()
 protected={}
 for e,m,k in base.targets():
  runtime=e.parent/'runtime'
  for folder in ['Save','CFG','AI']:
   for p in (runtime/folder).rglob('*'):
    if p.is_file():protected[str(p)]=b.sha(p)
  for p in runtime.iterdir():
   if p.is_file():protected[str(p)]=b.sha(p)
 base.OUT=OUT;base.BACK=BACK;base.install('movement_timing_iteration1')
 for e,m,k in base.targets():
  assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
  assert b.sha(e)==__import__('json').loads(m.read_text(encoding='utf-8'))['launcher_sha256']
 for path,digest in protected.items():assert b.sha(__import__('pathlib').Path(path))==digest,path
 base.write(OUT/'installed-verification.json',dict(result='passed',protected_files=len(protected),runtime_files_settings_saves_ai_unchanged=True,module_sha256=b.sha(OUT/'repath.dll')))

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
