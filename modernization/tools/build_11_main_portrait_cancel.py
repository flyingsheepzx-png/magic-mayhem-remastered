"""Preserve exact latest modules; correct main portrait right-click targeting."""
import argparse,json,shutil,subprocess
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
b=base.b
OUT=b.ROOT/'modernization/build/remastered-1.1-main-portrait-cancel'
BACK=b.ROOT/'modernization/backups/remastered-1.1-main-portrait-cancel'
SOURCE=b.ROOT/'modernization/build/remastered-1.1-options-render-v1'
LATEST=b.ROOT/'modernization/build/remastered-1.1-wrap-route-v1'

def build():
 current=resources(base.DEST/base.ENTRY)
 assert current==resources(LATEST/'release.exe')
 assert current[102]==(SOURCE/'qol_bindings.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.bin'):shutil.copy2(p,OUT/p.name)
 for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 for name in ['launcher.cpp','release_launcher.cpp']:shutil.copy2(LATEST/name,OUT/name)
 shutil.copy2(b.SRC/'main_portrait_input.inc',OUT/'main_portrait_input.inc')
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
 start=s.index('int __cdecl portrait_cast(unsigned flags){');end=s.index('void __cdecl native_portrait_cast(){',start)
 s=s[:start]+'#include "main_portrait_input.inc"\n'+s[end:]
 s=b.replace_once(s,'    jz native_portrait\n    call native_portrait_cast\n    xor eax,eax',
 '    jz native_portrait\n    cmp eax,1\n    jne consumed_portrait\n    call native_portrait_cast\nconsumed_portrait:\n    xor eax,eax')
 p.write_text(s,encoding='utf-8')
 base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 verify_resources()

def verify_resources():
 current=resources(LATEST/'release.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  assert all(r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name not in ('qol_bindings.cpp','launcher.cpp','release_launcher.cpp'):
   assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name

def install():
 verify_resources()
 v=json.loads((OUT/'verification.json').read_text())
 assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 assert (OUT/'main_portrait_input.inc').read_bytes()==(b.SRC/'main_portrait_input.inc').read_bytes()
 base.OUT=OUT;base.BACK=BACK;base.install('main_portrait_right_cancel')
 for e,m,k in base.targets():
  assert resources(e)[102]==(OUT/'qol_bindings.dll').read_bytes()
  assert b.sha(e)==json.loads(m.read_text(encoding='utf-8'))['launcher_sha256']

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
