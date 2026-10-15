"""Isolated search-budget diagnosis from exact latest resources."""
import shutil,json,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-save17-budget-probe'
old=b.ROOT/'modernization/build/remastered-1.1-dynamic-wait-v2';launch=b.ROOT/'modernization/build/remastered-1.1-options-render-v1'
current=resources(base.DEST/base.ENTRY);assert current[101]==(old/'repath.dll').read_bytes();assert current==resources(launch/'release.exe')
OUT.mkdir(exist_ok=False)
for f in old.iterdir():
 if f.suffix in ['.cpp','.h','.inc']:shutil.copy2(f,OUT/f.name)
for name in ['launcher.cpp','release_launcher.cpp','candidate.rc','release.rc','remastered.ico']:shutil.copy2(launch/name,OUT/name)
for i,name in [(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
f=OUT/'repath_multiunit_trial.cpp';s=f.read_text().replace('ds:[6df18ch],600','ds:[6df18ch],2400').replace('ds:[6df188h],601','ds:[6df188h],2401');f.write_text(s)
(OUT/'build.cmd').write_text((old/'build.cmd').read_text())
base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
