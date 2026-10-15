"""test18 captured-terrain correction, retaining all current 1.1 features."""
import argparse,shutil,subprocess
import build_11_short_direct as i
from install_11_minimap_v2 import resources
i.OUT=i.b.ROOT/'modernization/build/remastered-1.1-corridor'
i.BACK=i.b.ROOT/'modernization/backups/remastered-1.1-corridor'
def build():
 b=i.b;b.verify();source=b.ROOT/'modernization/build/remastered-1.1-short-direct'
 assert resources(i.ENTRY)[101]==(source/'repath.dll').read_bytes()
 assert resources(i.ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
 i.OUT.mkdir(exist_ok=False)
 for n in ['repath_multiunit_trial.cpp','render_replay_trial.cpp','clock_trial.cpp','logic_time_trial.cpp','game_time_trial.cpp','command_index.h','ui_layout.h','layout_context.h','launcher.cpp','combined.rc','qol_bindings.dll','build.cmd']:shutil.copy2(source/n,i.OUT/n)
 shutil.copy2(b.SRC/'corridor_route.inc',i.OUT/'corridor_route.inc')
 s=(source/'short_direct_route.inc').read_text();a=s.index('static int __cdecl short_direct_route(');z=s.index('__declspec(naked) static void short_direct_hook()',a)
 s=s[:a]+'''static bool corridor_route(void*,int,int,int,int*);
static int __cdecl short_direct_route(void* u,const unsigned* stack) {
 if(global(0x6df184)!=0 || field(u,0x618)!=0)return 0;
 int route[0x83];
 if(!corridor_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route))return 0;
 memcpy((void*)0x6c4bd0,route,sizeof(route));field(u,0xd03)=0;return 1;
}
'''+s[z:];(i.OUT/'short_direct_route.inc').write_text(s)
 p=i.OUT/'repath_multiunit_trial.cpp';s=p.read_text()
 def rep(a,c):
  nonlocal s
  assert s.count(a)==1,a;s=s.replace(a,c)
 rep('#include "short_direct_route.inc"','#include "short_direct_route.inc"\n#include "corridor_route.inc"')
 rep('static bool plan(void* u,int x,int y,int z,int* replacement) {','static bool plan(void* u,int x,int y,int z,int* replacement,bool loaded=false) {\n    if(corridor_route(u,x,y,z,replacement))return true;\n    if(loaded)return false;')
 rep('static void on_order_impl(void* u) {','static void on_order_impl(void* u,bool loaded=false) {')
 rep('field(u,0x618)!=1 || field(u,0xb6f)!=1','field(u,0x618)!=1 || (!loaded && field(u,0xb6f)!=1)')
 rep('if (!plan(u,goalx,goaly,goalz,replacement))','if (!plan(u,goalx,goaly,goalz,replacement,loaded))')
 rep('load_state(u,index);on_motion_impl(u);save_state(index);','load_state(u,index);\n    if(loaded_route_pending[index]){loaded_route_pending[index]=false;on_order_impl(u,true);}\n    on_motion_impl(u);save_state(index);')
 a=s.index('__declspec(naked) static void deserialize_hook()');z=s.index('__declspec(naked) static void request_hook()',a);part=s[a:z];assert part.count('call on_unit_replaced')==1
 s=s[:a]+part.replace('call on_unit_replaced','call on_unit_replaced\n        add esp,4\n        push dword ptr [esp+18h]\n        call mark_loaded_route')+s[z:]
 p.write_text(s);subprocess.run(['cmd','/c','build.cmd'],cwd=i.OUT,check=True)
 assert resources(i.OUT/i.ENTRY.name)[102]==resources(i.ENTRY)[102]
 b.write(i.OUT/'build-state.json',dict(launcher_before_sha256=b.sha(i.ENTRY),manifest_before_sha256=b.sha(i.MANIFEST)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);a=p.parse_args().action
 if a=='build':build()
 else:i.run(a)
