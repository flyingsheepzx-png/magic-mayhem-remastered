"""Isolated search-budget diagnosis from exact latest resources."""
import shutil,json,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-long-route-v2'
old=b.ROOT/'modernization/build/remastered-1.1-dynamic-wait-v2';launch=b.ROOT/'modernization/build/remastered-1.1-options-render-v1'
current=resources(base.DEST/base.ENTRY);assert current[101]==(old/'repath.dll').read_bytes();assert current==resources(launch/'release.exe')
OUT.mkdir(exist_ok=False)
for f in old.iterdir():
 if f.suffix in ['.cpp','.h','.inc']:shutil.copy2(f,OUT/f.name)
for name in ['launcher.cpp','release_launcher.cpp','candidate.rc','release.rc','remastered.ico']:shutil.copy2(launch/name,OUT/name)
for i,name in [(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
shutil.copy2(b.SRC/'long_route.inc',OUT/'long_route.inc')
f=OUT/'repath_multiunit_trial.cpp';s=f.read_text();s=b.replace_once(s,'#include "local_route.inc"','#include "local_route.inc"\n#include "long_route.inc"');s=b.replace_once(s,'local_route(u,x,y,z,replacement))','local_route(u,x,y,z,replacement) || long_route(u,x,y,z,replacement))');s=b.replace_once(s,'static void __cdecl on_unit_replaced(void* u) {','static void long_route_forget(void*);\nstatic void __cdecl on_unit_replaced(void* u) {\n    long_route_forget(u);');f.write_text(s)
f=OUT/'short_direct_route.inc';s=f.read_text();s=s.replace('static bool local_route(void*,int,int,int,int*);','static bool local_route(void*,int,int,int,int*);\nstatic bool long_route(void*,int,int,int,int*);');s=b.replace_once(s,'!local_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route))','!local_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route) &&\n    !long_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route))');f.write_text(s)
(OUT/'build.cmd').write_text((old/'build.cmd').read_text())
base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
