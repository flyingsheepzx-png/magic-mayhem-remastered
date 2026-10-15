"""Save14 first-chance AV fix, preserving current101/102/103 features."""
import argparse,shutil,json,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-reload-surface'
BACK=b.ROOT/'modernization/backups/remastered-1.1-reload-surface'
def build():
 source=b.ROOT/'modernization/build/remastered-1.1-minimap-units'
 launch=b.ROOT/'modernization/build/remastered-1.1-dynamic-wait-v2'
 current=resources(base.DEST/base.ENTRY);assert current==resources(launch/'candidate.exe')
 assert current[102]==(source/'qol_bindings.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in source.iterdir():
  if p.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico']:shutil.copy2(p,OUT/p.name)
 for name in ['launcher.cpp','release_launcher.cpp']:shutil.copy2(launch/name,OUT/name)
 for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'surface_lifecycle.cpp',OUT/'surface_lifecycle.cpp')
 base.OUT=OUT;base.native_fixture()
 cmd=(source/'build.cmd').read_text();needle='cl /nologo /LD'
 at=cmd.index(needle)
 cmd=cmd[:at]+'''cl /nologo /O2 /EHsc /std:c++17 surface_lifecycle_native_test.cpp surface_lifecycle_test_hooks.cpp /link /BASE:0x10000000 /DYNAMICBASE:NO /OUT:surface_lifecycle_native_test.exe
if errorlevel 1 exit /b 1
surface_lifecycle_native_test.exe
if errorlevel 1 exit /b 1
'''+cmd[at:]
 (OUT/'build.cmd').write_text(cmd);base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert r[101]==current[101] and r[103]==current[103] and r[102]==(OUT/'qol_bindings.dll').read_bytes()
 base.write(OUT/'verification.json',dict(result='passed',module_sha256=b.sha(OUT/'qol_bindings.dll'),native_surface_test=True,save14_reload_verified=False,scope='Exact native Destroy with null base/valid queried interface, duplicates,repeat lifecycle,palette cleanup'))
def install():
 v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['save14_reload_verified'] and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('reload_surface_lifecycle_fix')
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
