"""Stationary dynamic-obstacle reroute delta on the latest installed modules."""
import argparse,shutil,json,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-dynamic-wait-v2'
BACK=b.ROOT/'modernization/backups/remastered-1.1-dynamic-wait'

def build():
 old=b.ROOT/'modernization/build/remastered-1.1-occlusion-opacity'
 launch=b.ROOT/'modernization/build/remastered-1.1-minimap-units'
 current=resources(base.DEST/base.ENTRY)
 assert current==resources(launch/'candidate.exe')
 assert current[101]==(old/'repath.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in old.iterdir():
  if p.suffix in ['.cpp','.h','.inc']:shutil.copy2(p,OUT/p.name)
 for name in ['launcher.cpp','release_launcher.cpp','candidate.rc','release.rc','remastered.ico']:shutil.copy2(launch/name,OUT/name)
 for i,name in [(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'dynamic_wait.inc',OUT/'dynamic_wait.inc')
 p=OUT/'repath_multiunit_trial.cpp';s=p.read_text()
 s=b.replace_once(s,'int id,cursor,last_timer;','int id,cursor,last_timer,retry_cooldown;')
 s=b.replace_once(s,'static void __cdecl remember_blocked_wait(void* u) {','#include "dynamic_wait.inc"\nstatic void __cdecl remember_blocked_wait(void* u) {')
 s=b.replace_once(s,'s.identity=u;s.id=field(u,0);s.cursor=c;s.last_timer=7;', '''if(s.identity!=u || s.id!=field(u,0) ||
       memcmp(s.origin,(char*)u+8,12) || memcmp(s.goal,(char*)u+0x96b,12))s.retry_cooldown=0;
    s.identity=u;s.id=field(u,0);s.cursor=c;s.last_timer=field(u,0x66c);''')
 s=b.replace_once(s,'field(u,0x66c)=1;s.armed=false;\n    }','field(u,0x66c)=1;s.armed=false;\n    } else dynamic_wait_detour(u,s);')
 s=b.replace_once(s,'__declspec(naked) static void wait_tick_hook() {','''static DWORD dynamic_blocked_return=0x5112c3;
__declspec(naked) static void dynamic_blocked_wait_hook() {
    __asm {
        mov dword ptr [esi+66ch],5
        pushfd
        pushad
        push esi
        call remember_blocked_wait
        add esp,4
        popad
        popfd
        jmp dword ptr [dynamic_blocked_return]
    }
}
__declspec(naked) static void wait_tick_hook() {''')
 s=b.replace_once(s,'const unsigned char wait_bytes[]=', 'const unsigned char dynamic_blocked_bytes[]={0xc7,0x86,0x6c,0x06,0,0,0x05,0,0,0};\n        const unsigned char wait_bytes[]=')
 s=b.replace_once(s,'memcmp((void*)0x511bdd,blocked_bytes,10) ||','memcmp((void*)0x511bdd,blocked_bytes,10) ||\n            memcmp((void*)0x5112b9,dynamic_blocked_bytes,10) ||')
 s=b.replace_once(s,'if (!patch(0x511bdd,(void*)blocked_wait_hook,blocked_bytes,10)) return FALSE;', 'if (!patch(0x511bdd,(void*)blocked_wait_hook,blocked_bytes,10)) return FALSE;\n        if (!patch(0x5112b9,(void*)dynamic_blocked_wait_hook,dynamic_blocked_bytes,10)) return FALSE;')
 p.write_text(s)
 (OUT/'build.cmd').write_text((old/'build.cmd').read_text())
 base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert r[102]==current[102] and r[103]==current[103] and r[101]==(OUT/'repath.dll').read_bytes()

def install():
 v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['save14_runtime_verified'] and v['module_sha256']==b.sha(OUT/'repath.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('dynamic_obstacle_reroute_fix')

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
