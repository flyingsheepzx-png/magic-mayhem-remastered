"""Build/install isolated1.1 teammate portrait left-release casting."""
import argparse,json,shutil,subprocess
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources,replace
OUT=b.ROOT/'modernization/build/remastered-1.1-teammate-portrait'
BACK=b.ROOT/'modernization/backups/remastered-1.1-teammate-portrait-final'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'

def run(action):
 if action=='rollback':
  idle();v=json.loads((BACK/'installation.json').read_text(encoding='utf-8'))
  assert b.sha(ENTRY)==v['launcher_sha256'] and b.sha(MANIFEST)==v['manifest_sha256']
  for p in [ENTRY,MANIFEST]:replace(p,(BACK/p.name).read_bytes())
  b.verify();return
 b.verify()
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 if action=='build':
  src=b.ROOT/'modernization/build/remastered-1.1-window-close'
  assert resources(ENTRY)[102]==(src/'qol_bindings.dll').read_bytes()
  assert resources(ENTRY)[101]==(src/'repath.dll').read_bytes()
  OUT.mkdir(exist_ok=False)
  for n in ['qol_bindings.cpp','mixed_ui_fonts.cpp','campaign_ui.cpp','port_drag.cpp','confirm_dialog.cpp','qwen_highlight.cpp','layout_context.h','ui_geometry.h','window_close.cpp','combined.rc','launcher.cpp','build.cmd','repath.dll']:shutil.copy2(src/n,OUT/n)
  shutil.copy2(b.SRC/'teammate_portrait.inc',OUT/'teammate_portrait.inc')
  p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
  s=b.replace_once(s,'bool install() {','#include "teammate_portrait.inc"\nbool install() {\n    if(memcmp((void*)0x463030,teammate_original,sizeof(teammate_original)))return false;')
  old='    return true;\n}\n}\nextern "C" bool mm_install_mixed_fonts();'
  new='''    site=reinterpret_cast<void*>(0x463030);
    if(!VirtualProtect(site,10,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char teammate_patch[]={0xe9,0,0,0,0,0x90,0x90,0x90,0x90,0x90};
    *reinterpret_cast<int*>(teammate_patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(teammate_mouse_hook)-0x463030-5);
    memcpy(site,teammate_patch,10);FlushInstructionCache(GetCurrentProcess(),site,10);
    VirtualProtect(site,10,old,&unused);
'''+old
  s=b.replace_once(s,old,new);p.write_text(s,encoding='utf-8')
  subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
  before=resources(ENTRY);after=resources(OUT/ENTRY.name)
  assert {k:v for k,v in before.items() if k!=102}=={k:v for k,v in after.items() if k!=102}
  b.write(OUT/'build-state.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST),sources={n:b.sha(OUT/n) for n in ['qol_bindings.cpp','teammate_portrait.inc']}))
 else:
  idle();v=json.loads((OUT/'build-state.json').read_text(encoding='utf-8'));t=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
  assert t['result']=='passed' and t['module_sha256']==b.sha(OUT/'qol_bindings.dll')
  assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  BACK.mkdir(exist_ok=False);before={p:p.read_bytes() for p in [ENTRY,MANIFEST]}
  for p,raw in before.items():(BACK/p.name).write_bytes(raw)
  inv=b.inventory(b.TARGET/'runtime');m=json.loads(before[MANIFEST]);m['launcher_sha256']=b.sha(OUT/ENTRY.name)
  m['teammate_portrait_fix']=dict(verification=t,backup=str(BACK),acceptance='offline native adapter checks passed; user test18 acceptance pending')
  try:
   replace(ENTRY,(OUT/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode())
   assert b.inventory(b.TARGET/'runtime')==inv;b.verify()
  except BaseException:
   for p,raw in before.items():replace(p,raw)
   raise
  b.write(BACK/'installation.json',dict(launcher_sha256=b.sha(ENTRY),manifest_sha256=b.sha(MANIFEST)))
 print(action,'teammate portrait passed')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
