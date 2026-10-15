"""Save3 local routing delta based on current installed 1.1 modules."""
import argparse,shutil,subprocess,json
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-local-route'
BACK=b.ROOT/'modernization/backups/remastered-1.1-local-route'
def build():
 OUT.mkdir(exist_ok=False);old=b.ROOT/'modernization/build/remastered-1.1-corridor'
 for p in old.iterdir():
  if p.suffix in ('.cpp','.h','.inc'):shutil.copy2(p,OUT/p.name)
 current=resources(b.TARGET/'MagicMayhem-Remastered-1.1.exe');assert current[101]==(old/'repath.dll').read_bytes()
 (OUT/'qol_bindings.dll').write_bytes(current[102])
 shutil.copy2(b.SRC/'local_route.inc',OUT/'local_route.inc')
 source=OUT/'repath_multiunit_trial.cpp';s=source.read_text()
 s=b.replace_once(s,'#include "corridor_route.inc"','#include "corridor_route.inc"\n#include "local_route.inc"')
 s=b.replace_once(s,'if(corridor_route(u,x,y,z,replacement))return true;','if(corridor_route(u,x,y,z,replacement) || local_route(u,x,y,z,replacement))return true;')
 s=b.replace_once(s,'{log_event("same_first_step",u);return;}','{\n        if(loaded){\n            // Keep current segment reservation, animation and interpolation.\n            // Replace only the continuation when the first edge is identical.\n            memcpy(replacement+5,oldpoint,28);\n            memcpy((char*)u+0x96b,replacement,sizeof(replacement));\n            field(u,0xd03)=0;log_event("loaded_same_edge_route",u);\n        }\n        log_event("same_first_step",u);return;\n    }')
 source.write_text(s)
 p=OUT/'short_direct_route.inc';s=p.read_text();s=s.replace('static bool corridor_route(void*,int,int,int,int*);','static bool corridor_route(void*,int,int,int,int*);\nstatic bool local_route(void*,int,int,int,int*);')
 s=b.replace_once(s,'if(!corridor_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route))return 0;','if(!corridor_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route) &&\n    !local_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route))return 0;');p.write_text(s)
 for n in ['launcher.cpp','release_launcher.cpp','candidate.rc','release.rc','remastered.ico']:shutil.copy2(b.ROOT/'modernization/build/remastered-1.1-character-icons'/n,OUT/n)
 cmd=(old/'build.cmd').read_text();cmd=cmd[:cmd.index('rc /nologo')]+'''rc /nologo /focandidate.res candidate.rc
if errorlevel 1 exit /b 1
rc /nologo /forelease.res release.rc
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:candidate.exe bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER release_launcher.cpp release.res /link /SUBSYSTEM:WINDOWS /OUT:release.exe bcrypt.lib user32.lib
'''
 (OUT/'build.cmd').write_text(cmd);subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for n in ['candidate.exe','release.exe']:assert resources(OUT/n)[102]==current[102]
 base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
def run(action):
 if action=='build':build();return
 v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed'
 if action=='install':assert v.get('save3_runtime_verified')
 base.OUT=OUT;base.BACK=BACK
 if action=='install':base.install('local_route_fix')
 else:base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
