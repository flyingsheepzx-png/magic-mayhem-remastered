"""Extend the installed reload-surface build, preserving all current modules."""
import argparse,json,shutil,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-portrait-ready'
BACK=b.ROOT/'modernization/backups/remastered-1.1-portrait-ready'
def build():
 source=b.ROOT/'modernization/build/remastered-1.1-reload-surface'
 current=resources(base.DEST/base.ENTRY)
 assert current==resources(source/'candidate.exe')
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in source.iterdir():
  if p.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico','.bin']:shutil.copy2(p,OUT/p.name)
 for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'portrait_sprite_ready.cpp',OUT/'portrait_sprite_ready.cpp')
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
 s=b.replace_once(s,'extern "C" bool mm_install_surface_lifecycle();','extern "C" bool mm_install_surface_lifecycle();\nextern "C" bool mm_install_portrait_sprite_ready();')
 s=b.replace_once(s,'return mm_install_surface_lifecycle() && install()','return mm_install_surface_lifecycle() && mm_install_portrait_sprite_ready() && install()');p.write_text(s,encoding='utf-8')
 p=OUT/'build.cmd';p.write_text(b.replace_once(p.read_text(),'window_close.cpp surface_lifecycle.cpp /link','window_close.cpp surface_lifecycle.cpp portrait_sprite_ready.cpp /link'))
 base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert r[101]==current[101] and r[103]==current[103] and r[102]==(OUT/'qol_bindings.dll').read_bytes()
 subprocess.run([__import__('sys').executable,str(b.ROOT/'modernization/tests/portrait_sprite_ready_test.py')],check=True)
def install():
 v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('portrait_sprite_readiness_fix')
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
