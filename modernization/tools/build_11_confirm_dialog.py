"""Preserve all installed 1.1 modules while adapting common modal layout."""
import argparse,json,shutil,subprocess,struct,hashlib
from pathlib import Path
from PIL import Image
import pefile
import build_remastered_11 as b
import seedvr_ui_11 as s
from install_11_minimap_v2 import idle,resources
from build_11_campaign_ui import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-confirm-dialog'
BACK=b.ROOT/'modernization/backups/remastered-1.1-confirm-dialog'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json';RT=b.TARGET/'runtime'
REL='Bitmaps/hd-ui/dlgback 800x600.PNG'
def run(action):
 if action=='rollback':
  idle();r=json.loads((BACK/'installation.json').read_text(encoding='utf-8'))
  for row in r['files']:assert b.sha(b.ROOT/row['path'])==row['sha256']
  for row in r['files']:
   p=b.ROOT/row['path'];old=BACK/'project'/row['path']
   if old.exists():replace(p,old.read_bytes())
   else:p.unlink()
  b.verify();return
 b.verify();assert b.sha(RT/'Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 pe=pefile.PE(str(RT/'Chaos-Wide169-engine.exe'));image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
 assert image[0x4cf3b0-base:0x4cf3b7-base]==bytes.fromhex('6aff68c21c5c00')
 for site in [0x4cf45e,0x4cf491]:assert image[site-base]==0xe8 and site+5+struct.unpack_from('<i',image,site-base+1)[0]==0x486ae0
 if action=='build':
  OUT.mkdir(exist_ok=True);source=b.ROOT/'modernization/build/remastered-1.1-port-drag'
  assert resources(ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
  for n in ['qol_bindings.cpp','mixed_ui_fonts.cpp','campaign_ui.cpp','port_drag.cpp','layout_context.h','ui_geometry.h','repath.dll','combined.rc']:shutil.copy2(source/n,OUT/n)
  shutil.copy2(b.ROOT/'modernization/build/remastered-1.1-book-open/launcher.cpp',OUT/'launcher.cpp')
  shutil.copy2(b.SRC/'confirm_dialog.cpp',OUT/'confirm_dialog.cpp')
  q=(OUT/'qol_bindings.cpp').read_text();needle='&& mm_install_port_drag()?TRUE:FALSE;';assert q.count(needle)==1
  q=q.replace('extern "C" bool mm_install_port_drag();','extern "C" bool mm_install_port_drag();\nextern "C" bool mm_install_confirm_dialog();').replace(needle,'&& mm_install_port_drag() && mm_install_confirm_dialog()?TRUE:FALSE;');(OUT/'qol_bindings.cpp').write_text(q)
  cmd=(source/'build.cmd').read_text().replace('port_drag.cpp /link','port_drag.cpp confirm_dialog.cpp /link')
  if 'port_drag_test.cpp' in cmd:cmd=cmd[:cmd.index('if errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 port_drag_test.cpp')]
  (OUT/'build.cmd').write_text(cmd);subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
  assert resources(ENTRY)[101]==resources(OUT/ENTRY.name)[101]
  bitmap=RT/'Bitmaps/dlgback 800x600.PNG';old=Image.open(bitmap);assert old.size==(416,280)
  # This common bitmap has no generated task in the approved SeedVR pack.
  old.convert('RGB').resize((832,560),Image.Resampling.LANCZOS).save(OUT/'dialog.PNG')
  b.write(OUT/'verification.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST),bitmap=[832,560],source_sha256=b.sha(bitmap),art_method='Lanczos2x original common-dialog bitmap; no model substitution',engine_unchanged=True,resource101_unchanged=True,sites=['4cf3b0','4cf45e','4cf491']))
 else:
  idle();v=json.loads((OUT/'verification.json').read_text());assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  m=json.loads(MANIFEST.read_text(encoding='utf-8'));assert not (RT/REL).exists();m['launcher_sha256']=b.sha(OUT/ENTRY.name);m['files'][REL]=b.sha(OUT/'dialog.PNG');m['confirm_dialog_geometry']=v
  updates={ENTRY:(OUT/ENTRY.name).read_bytes(),RT/REL:(OUT/'dialog.PNG').read_bytes(),MANIFEST:(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()}
  BACK.mkdir(exist_ok=False);before={p:p.read_bytes() if p.exists() else None for p in updates};rows=[]
  for p,raw in before.items():
   rel=p.relative_to(b.ROOT).as_posix();rows.append(dict(path=rel,sha256=hashlib.sha256(updates[p]).hexdigest()))
   if raw is not None:out=BACK/'project'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
  b.write(BACK/'installation.json',dict(files=rows))
  try:
   for p,raw in updates.items():p.parent.mkdir(parents=True,exist_ok=True);replace(p,raw)
   b.verify()
  except BaseException:
   for p,raw in before.items():
    if raw is None:p.unlink(missing_ok=True)
    else:replace(p,raw)
   raise
 print(action,'confirmation passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
