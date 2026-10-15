"""Hash-gated Alt+F4 close lifecycle, isolated launcher resource102 only."""
import argparse,json,shutil,subprocess
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources,replace
OUT=b.ROOT/'modernization/build/remastered-1.1-window-close'
BACK=b.ROOT/'modernization/backups/remastered-1.1-window-close'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'
def run(action):
 if action=='rollback':
  idle();v=json.loads((BACK/'installation.json').read_text());assert b.sha(ENTRY)==v['launcher_sha256'] and b.sha(MANIFEST)==v['manifest_sha256']
  for p in [ENTRY,MANIFEST]:replace(p,(BACK/p.name).read_bytes())
  b.verify();return
 b.verify()
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 if action=='build':
  source=b.ROOT/'modernization/build/remastered-1.1-minimap-center'
  path=b.ROOT/'modernization/build/remastered-1.1-corridor'
  assert resources(ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
  assert resources(ENTRY)[101]==(path/'repath.dll').read_bytes()
  OUT.mkdir(exist_ok=False)
  for n in ['qol_bindings.cpp','mixed_ui_fonts.cpp','campaign_ui.cpp','port_drag.cpp','confirm_dialog.cpp','qwen_highlight.cpp','layout_context.h','ui_geometry.h','combined.rc','launcher.cpp','build.cmd']:shutil.copy2(source/n,OUT/n)
  shutil.copy2(path/'repath.dll',OUT/'repath.dll');shutil.copy2(b.SRC/'window_close.cpp',OUT/'window_close.cpp')
  p=OUT/'qol_bindings.cpp';s=p.read_text();old='extern "C" bool mm_install_confirm_dialog();';assert s.count(old)==1;s=s.replace(old,old+'\nextern "C" bool mm_install_window_close();')
  old='&& mm_install_confirm_dialog()?TRUE:FALSE;';assert s.count(old)==1;s=s.replace(old,'&& mm_install_confirm_dialog() && mm_install_window_close()?TRUE:FALSE;');p.write_text(s)
  p=OUT/'build.cmd';s=p.read_text();old='qwen_highlight.cpp /link';assert s.count(old)==1;s=s.replace(old,'qwen_highlight.cpp window_close.cpp /link');p.write_text(s)
  subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
  assert resources(OUT/ENTRY.name)[101]==resources(ENTRY)[101]
  b.write(OUT/'build-state.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST)))
 else:
  idle();v=json.loads((OUT/'build-state.json').read_text());t=json.loads((OUT/'verification.json').read_text());assert t['result']=='passed' and t['module_sha256']==b.sha(OUT/'qol_bindings.dll')
  assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  BACK.mkdir(exist_ok=False);before={p:p.read_bytes() for p in [ENTRY,MANIFEST]}
  for p,raw in before.items():(BACK/p.name).write_bytes(raw)
  m=json.loads(before[MANIFEST]);m['launcher_sha256']=b.sha(OUT/ENTRY.name);m['window_close_fix']=dict(verification=t,backup=str(BACK),acceptance='offline passed; user exit acceptance pending')
  try:
   replace(ENTRY,(OUT/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());b.verify()
  except BaseException:
   for p,raw in before.items():replace(p,raw)
   raise
  b.write(BACK/'installation.json',dict(launcher_sha256=b.sha(ENTRY),manifest_sha256=b.sha(MANIFEST)))
 print(action,'window close passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
