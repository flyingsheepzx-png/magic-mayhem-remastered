"""Retain budget300 and all current modules; install one perception iteration."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-danger-refresh'
BACK=b.ROOT/'modernization/backups/remastered-1.1-danger-refresh'
SOURCE=b.ROOT/'modernization/build/remastered-1.1-ai-budget300'
ENGINE='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(SOURCE/'candidate.exe')
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']==ENGINE
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.bin'):shutil.copy2(p,OUT/p.name)
 for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'ai_danger_refresh.cpp',OUT/'ai_danger_refresh.cpp')
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
 s=b.replace_once(s,'extern "C" bool mm_install_ai_budget();','extern "C" bool mm_install_ai_budget();\nextern "C" bool mm_install_ai_danger_refresh();')
 s=b.replace_once(s,'return mm_install_ai_budget() &&','return mm_install_ai_danger_refresh() && mm_install_ai_budget() &&');p.write_text(s,encoding='utf-8')
 p=OUT/'build.cmd';p.write_text(b.replace_once(p.read_text(),'ai_budget.cpp /link','ai_budget.cpp ai_danger_refresh.cpp /link'))
 base.write(OUT/'before.json',rows);subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()
def verify():
 current=resources(SOURCE/'candidate.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  for i in current:assert r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i])
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name!='qol_bindings.cpp':assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
 subprocess.run([sys.executable,str(b.ROOT/'modernization/tests/ai_danger_refresh_test.py')],check=True)
def install():
 v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
 assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 current=resources(SOURCE/'candidate.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  for i in current:assert r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i])
 base.OUT=OUT;base.BACK=BACK;base.install('singleplayer_danger_refresh')
 for e,m,k in base.targets():
  assert resources(e)[102]==(OUT/'qol_bindings.dll').read_bytes()
  assert b.sha(e)==json.loads(m.read_text(encoding='utf-8'))['launcher_sha256']
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify','install','rollback']);globals()[p.parse_args().action]()
