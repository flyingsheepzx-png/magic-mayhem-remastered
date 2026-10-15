"""Build from exact installed long-route-v2, retaining options/AI modules."""
import shutil,subprocess
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
b=base.b
OUT=b.ROOT/'modernization/build/remastered-1.1-command-response-v1'
OLD=b.ROOT/'modernization/build/remastered-1.1-long-route-v2'
current=resources(base.DEST/base.ENTRY)
assert current==resources(OLD/'release.exe')
OUT.mkdir(exist_ok=False)
for f in OLD.iterdir():
 if f.suffix in ('.cpp','.h','.inc','.rc','.ico') or f.name=='build.cmd':shutil.copy2(f,OUT/f.name)
for i,name in [(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
shutil.copy2(b.SRC/'command_response.inc',OUT/'command_response.inc')
p=OUT/'repath_multiunit_trial.cpp';s=p.read_text()
s=b.replace_once(s,'int* replacement,bool loaded=false) {','int* replacement,bool loaded=false,bool combat=false) {')
s=b.replace_once(s,' || long_route(u,x,y,z,replacement))',' || (!combat && long_route(u,x,y,z,replacement)))')
s=b.replace_once(s,'static void on_order_impl(void* u,bool loaded=false) {','static bool on_order_impl(void* u,bool loaded=false,bool combat=false) {')
s=b.replace_once(s,'plan(u,goalx,goaly,goalz,replacement,loaded)','plan(u,goalx,goaly,goalz,replacement,loaded,combat)')
a=s.index('static bool on_order_impl(');end=s.index('static void on_motion_impl(',a)
chunk=s[a:end].replace('return;','return false;')
chunk=b.replace_once(chunk,'check_ownership(u,dx,dy,dz);','check_ownership(u,dx,dy,dz);\n    return true;')
s=s[:a]+chunk+'#include "command_response.inc"\n\n'+s[end:]
s=b.replace_once(s,'load_state(u,index);on_order_impl(u);save_state(index);','load_state(u,index);if(!pursuit_to_move(u))on_order_impl(u);save_state(index);')
s=b.replace_once(s,'if (!patch(0x50fcec,(void*)order_hook,a,6)) return FALSE;','if (!patch(0x50fcec,(void*)order_hook,a,6)) return FALSE;\n        const unsigned char attack_bytes[]={0xe8,0x39,0xfb,0xff,0xff};\n        if (!patch(0x50aef2,(void*)attack_response_hook,attack_bytes,5)) return FALSE;')
p.write_text(s)
base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
