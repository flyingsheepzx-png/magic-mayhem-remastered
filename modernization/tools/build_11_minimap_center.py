"""Correct scanner click layout width without changing storage pitch."""
import argparse,json,shutil,subprocess
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources,replace
OUT=b.ROOT/'modernization/build/remastered-1.1-minimap-center'
BACK=b.ROOT/'modernization/backups/remastered-1.1-minimap-center'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
MANIFEST=b.TARGET/'manifest.json'

def run(action):
 if action=='rollback':
  idle();s=json.loads((BACK/'installation.json').read_text())
  assert b.sha(ENTRY)==s['launcher_sha256'] and b.sha(MANIFEST)==s['manifest_sha256']
  for p in [ENTRY,MANIFEST]:replace(p,(BACK/p.name).read_bytes())
  b.verify();return
 b.verify()
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 if action=='build':
  source=b.ROOT/'modernization/build/remastered-1.1-qwen-highlight'
  assert resources(ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
  OUT.mkdir(exist_ok=False)
  for n in ['qol_bindings.cpp','mixed_ui_fonts.cpp','campaign_ui.cpp','port_drag.cpp','confirm_dialog.cpp','qwen_highlight.cpp','layout_context.h','ui_geometry.h','repath.dll','combined.rc','launcher.cpp','build.cmd']:shutil.copy2(source/n,OUT/n)
  p=OUT/'mixed_ui_fonts.cpp';s=p.read_text()
  marker='__declspec(naked) void scanner_refresh_width_hook()'
  assert s.count(marker)==1
  s=s.replace(marker,'// Main object +0xeb aliases secondary +0xca (storage width).\n// The click inverse must use the same logical width as scanner drawing.\n__declspec(naked) void scanner_click_width_hook(){__asm{\n    mov ebp,dword ptr [scanner_layout_width]\n    push 555f23h\n    ret\n}}\n'+marker)
  marker='memcmp((void*)0x555b90,"\\x8b\\x8e\\xe2\\x00\\x00\\x00",6))'
  assert s.count(marker)==1
  s=s.replace(marker,'memcmp((void*)0x555f1d,"\\x8b\\xab\\xeb\\x00\\x00\\x00",6) ||\n       '+marker)
  marker='return expand_cursor_surface() && patch(0x554b06,scanner_width_hook)'
  assert s.count(marker)==1
  s=s.replace(marker,'return expand_cursor_surface() && patch(0x555f1d,scanner_click_width_hook) && patch(0x554b06,scanner_width_hook)')
  p.write_text(s)
  subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
  assert resources(ENTRY)[101]==resources(OUT/ENTRY.name)[101]
  b.write(OUT/'build-state.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST)))
 else:
  idle();v=json.loads((OUT/'build-state.json').read_text());checks=json.loads((OUT/'center-verification.json').read_text())
  assert checks['result']=='passed' and checks['qol_sha256']==b.sha(OUT/'qol_bindings.dll')
  assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  BACK.mkdir(exist_ok=False)
  before={p:p.read_bytes() for p in [ENTRY,MANIFEST]}
  for p,raw in before.items():(BACK/p.name).write_bytes(raw)
  m=json.loads(before[MANIFEST]);m['launcher_sha256']=b.sha(OUT/ENTRY.name)
  m['minimap_click_center_fix']=dict(verification=checks,backup=str(BACK),acceptance='offline passed; user gameplay pending')
  try:
   replace(ENTRY,(OUT/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());b.verify()
  except BaseException:
   for p,raw in before.items():replace(p,raw)
   raise
  b.write(BACK/'installation.json',dict(launcher_sha256=b.sha(ENTRY),manifest_sha256=b.sha(MANIFEST)))
 print(action,'minimap click width passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
