"""Iteration2: momentum continuity after native segment safety checks."""
import argparse,json,shutil,subprocess
import build_11_pick_projection as prev
import build_11_movement_timing as timing
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-movement-momentum'
BACK=b.ROOT/'modernization/backups/remastered-1.1-movement-momentum'
SOURCE=timing.OUT;LATEST=prev.OUT
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(LATEST/'release.exe')
 assert current[101]==(SOURCE/'repath.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  j=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==j['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==j['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.dll'):shutil.copy2(p,OUT/p.name)
 for n in ['launcher.cpp','release_launcher.cpp']:shutil.copy2(LATEST/n,OUT/n)
 for i,n in [(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/n).write_bytes(current[i])
 shutil.copy2(b.SRC/'movement_momentum.cpp',OUT/'movement_momentum.cpp')
 p=OUT/'repath_multiunit_trial.cpp';s=p.read_text()
 s='extern "C" bool __cdecl mm_install_movement_momentum();\nextern "C" void __cdecl mm_momentum_redirect_begin(void*);\nextern "C" void __cdecl mm_momentum_redirect_end();\n'+s
 s=b.replace_once(s,'    field(u,0x618)=0;field(u,0xb6f)=0;field(u,0x5f0)=0;','    mm_momentum_redirect_begin(u);\n    field(u,0x618)=0;field(u,0xb6f)=0;field(u,0x5f0)=0;')
 s=b.replace_once(s,'    ((UnitFn)0x510e80)(u);','    ((UnitFn)0x510e80)(u);\n    mm_momentum_redirect_end();')
 s=b.replace_once(s,'        if (!mm_logic_time_initialize(h) || !mm_game_time_initialize(h)) return FALSE;','        if (!mm_logic_time_initialize(h) || !mm_game_time_initialize(h) || !mm_install_movement_momentum()) return FALSE;')
 p.write_text(s)
 p=OUT/'build.cmd';s=p.read_text().replace('game_time_trial.cpp /link','game_time_trial.cpp movement_momentum.cpp /link');p.write_text(s)
 base.write(OUT/'before.json',rows);subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()
def verify():
 current=resources(LATEST/'release.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  assert all(r[i]==((OUT/'repath.dll').read_bytes() if i==101 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name not in ('repath_multiunit_trial.cpp','launcher.cpp','release_launcher.cpp'):assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
 for n in ['launcher.cpp','release_launcher.cpp']:assert (OUT/n).read_bytes()==(LATEST/n).read_bytes()
def install():
 verify();v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'repath.dll')
 t=json.loads((OUT/'timing-preservation.json').read_text());assert t['result']=='passed' and t['module_sha256']==v['module_sha256']
 assert len(v['regressions'])==4 and sum(r['checks'] for r in v['regressions'])==162
 assert (OUT/'movement_momentum.cpp').read_bytes()==(b.SRC/'movement_momentum.cpp').read_bytes()
 from pathlib import Path
 protected={}
 for e,m,k in base.targets():
  rt=e.parent/'runtime'
  for folder in ['Save','CFG','AI']:
   for p in (rt/folder).rglob('*'):
    if p.is_file():protected[str(p)]=b.sha(p)
  for p in rt.iterdir():
   if p.is_file():protected[str(p)]=b.sha(p)
 base.OUT=OUT;base.BACK=BACK;base.install('movement_momentum_iteration2')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
 for path,digest in protected.items():assert b.sha(Path(path))==digest,path
 base.write(OUT/'installed-verification.json',dict(result='passed',protected_files=len(protected),runtime_files_settings_saves_ai_unchanged=True))
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
