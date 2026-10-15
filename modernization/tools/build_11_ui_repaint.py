"""Incremental resource-102 fixes, preserving installed campaign and runtime bytes."""
from pathlib import Path
import argparse,json,shutil,subprocess,struct
import pefile
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources
from build_11_campaign_ui import replace
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
MANIFEST=b.TARGET/'manifest.json'
ENGINE=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
SHA='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
def run(action):
 out=b.ROOT/'modernization/build/remastered-1.1-port-drag'
 back=b.ROOT/'modernization/backups/remastered-1.1-port-drag'
 if action=='rollback':
  idle();r=json.loads((back/'installation.json').read_text());assert b.sha(ENTRY)==r['launcher_sha256']
  replace(ENTRY,(back/ENTRY.name).read_bytes());replace(MANIFEST,(back/MANIFEST.name).read_bytes());b.verify();return
 b.verify();assert b.sha(ENGINE)==SHA
 baseline=json.loads((b.ROOT/'modernization/current-baseline.json').read_text())['latest_development']
 for rel,digest in baseline['files'].items():
  if rel.startswith(('game/','game-wide169/')):assert b.sha(b.ROOT/rel)==digest,rel
 installed=json.loads((b.ROOT/baseline['installed_manifest']).read_text())
 assert installed
 pe=pefile.PE(str(ENGINE));image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
 assert image[0x576830-base:0x576836-base]==bytes.fromhex('81ec00020000')
 assert struct.unpack_from('<4i',image,0x5c774c-base)==(83,66,83,66)
 from spr_assets import read_spr
 _,frames=read_spr(b.TARGET/'runtime/Interface/SpellBox/800x600/mitems.spr')
 assert len(frames)==23 and max(f['width'] for f in frames)<=166 and max(f['height'] for f in frames)<=166
 if action=='build':
  source=b.ROOT/'modernization/build/remastered-1.1-campaign-ui'
  assert resources(ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
  out.mkdir(exist_ok=False)
  for n in ['qol_bindings.cpp','mixed_ui_fonts.cpp','campaign_ui.cpp','layout_context.h','ui_geometry.h','launcher.cpp','repath.dll','combined.rc']:shutil.copy2(source/n,out/n)
  shutil.copy2(b.SRC/'port_drag.cpp',out/'port_drag.cpp')
  shutil.copy2(b.SRC/'port_drag_test.cpp',out/'port_drag_test.cpp')
  q=(out/'qol_bindings.cpp').read_text();needle='&& mm_install_campaign_ui()?TRUE:FALSE;';assert q.count(needle)==1
  q=q.replace('extern "C" bool mm_install_campaign_ui();','extern "C" bool mm_install_campaign_ui();\nextern "C" bool mm_install_port_drag();')
  q=q.replace(needle,'&& mm_install_campaign_ui() && mm_install_port_drag()?TRUE:FALSE;');(out/'qol_bindings.cpp').write_text(q)
  cmd=(source/'build.cmd').read_text().replace('campaign_ui.cpp /link','campaign_ui.cpp port_drag.cpp /link')
  cmd+='if errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 port_drag_test.cpp /link /OUT:port_drag_test.exe\nif errorlevel 1 exit /b 1\nport_drag_test.exe\n'
  (out/'build.cmd').write_text(cmd);subprocess.run(['cmd','/c','build.cmd'],cwd=out,check=True)
  assert resources(ENTRY)[101]==resources(out/ENTRY.name)[101]
  b.write(out/'verification.json',dict(engine_sha256=SHA,launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST),frames=23,drag_canvas=[166,166],resource101_unchanged=True,native_entry_bytes='81ec00020000',native_table=[83,66,83,66],runtime_acceptance='pending user testing'))
 elif action=='install':
  idle();v=json.loads((out/'verification.json').read_text());assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  assert resources(ENTRY)[101]==resources(out/ENTRY.name)[101]
  m=json.loads(MANIFEST.read_text());back.mkdir(exist_ok=False)
  for p in [ENTRY,MANIFEST]:shutil.copy2(p,back/p.name)
  m['launcher_sha256']=b.sha(out/ENTRY.name);m['port_drag_geometry']=v
  try:
   replace(ENTRY,(out/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());b.verify()
  except BaseException:
   for p in [ENTRY,MANIFEST]:replace(p,(back/p.name).read_bytes())
   raise
  b.write(back/'installation.json',dict(launcher_sha256=b.sha(ENTRY),runtime_unchanged=True))
 print(action,'port drag passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
