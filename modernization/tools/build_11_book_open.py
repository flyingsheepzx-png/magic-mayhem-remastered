"""Cover-only geometry and loader extension atop the installed drag fix."""
import argparse,json,shutil,subprocess,struct,hashlib
from pathlib import Path
from PIL import Image
import pefile
import build_remastered_11 as b
import seedvr_ui_11 as s
from install_11_minimap_v2 import idle,resources
from build_11_campaign_ui import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-book-open'
BACK=b.ROOT/'modernization/backups/remastered-1.1-book-open'
RT=b.TARGET/'runtime';ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'
REL='Interface/Grimoire/800x600/ClosedBook.PNG'
def main(action):
 if action=='rollback':
  idle();r=json.loads((BACK/'installation.json').read_text())
  for row in r['files']:assert b.sha(b.ROOT/row['path'])==row['sha256']
  for row in r['files']:
   target=b.ROOT/row['path'];old=BACK/'project'/row['path']
   if old.exists():replace(target,old.read_bytes())
   else:target.unlink()
  b.verify();return
 b.verify();assert b.sha(RT/'Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 pe=pefile.PE(str(RT/'Chaos-Wide169-engine.exe'));data=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
 for site,target in [(0x4c3d7e,0x58d320),(0x4c3dcc,0x58d1a0)]:assert data[site-base]==0xe8 and site+5+struct.unpack_from('<i',data,site-base+1)[0]==target
 if action=='build':
  OUT.mkdir(exist_ok=False)
  source=b.ROOT/'modernization/build/remastered-1.1-port-drag'
  assert resources(ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
  for name in ['launcher.cpp','repath.dll','qol_bindings.dll','combined.rc']:shutil.copy2(source/name,OUT/name)
  shutil.copy2(b.SRC/'png_grimoire.cpp',OUT/'png_grimoire.cpp')
  cmd='@echo off\ncall "'+str(b.VC)+'" x86 >nul\ncl /nologo /LD /MT /O2 /EHsc /std:c++17 png_grimoire.cpp /link /OUT:png_pages.dll ole32.lib windowscodecs.lib gdi32.lib\nif errorlevel 1 exit /b 1\n'
  (OUT/'module.cmd').write_text(cmd);subprocess.run(['cmd','/c','module.cmd'],cwd=OUT,check=True)
  old=b.sha(RT/'png_pages.dll');text=(OUT/'launcher.cpp').read_text();assert text.count(old)==1
  (OUT/'launcher.cpp').write_text(text.replace(old,b.sha(OUT/'png_pages.dll')))
  cmd=(source/'build.cmd').read_text();cmd=cmd[cmd.index('rc /nologo'):];cmd=cmd[:cmd.index('if errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 port_drag_test.cpp')] if 'port_drag_test.cpp' in cmd else cmd
  (OUT/'launcher.cmd').write_text('@echo off\ncall "'+str(b.VC)+'" x86 >nul\n'+cmd);subprocess.run(['cmd','/c','launcher.cmd'],cwd=OUT,check=True)
  assert resources(ENTRY)==resources(OUT/ENTRY.name)
  plan=json.loads(s.PLAN.read_text());a=next(a for a in plan['assets'] if a['path'].endswith('800x600/ClosedBook.JPG'))
  task=next(t for t in plan['tasks'] if t['id']==a['task']);assert b.sha(Path(task['output']))==task['output_sha256']
  image=Image.open(task['output']).convert('RGB').resize((1920,1440),Image.Resampling.LANCZOS)
  result=Image.new('RGB',(2560,1440));result.paste(image,(320,0));result.save(OUT/'ClosedBook.PNG')
  assert result.crop((0,0,320,1440)).getbbox() is None and result.crop((2240,0,2560,1440)).getbbox() is None
  assert result.crop((320,0,2240,1440)).tobytes()==image.tobytes()
  b.write(OUT/'verification.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST),png_before_sha256=old,model_output_sha256=task['output_sha256'],canvas=[2560,1440],content=[1920,1440],origin=[320,0],resources_unchanged=True,black_sidebars_exact=True,content_pixels_exact=True,loader_sites=['4c3d7e','4c3dcc'],runtime_acceptance='pending user testing'))
 else:
  idle();v=json.loads((OUT/'verification.json').read_text());assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256'] and b.sha(RT/'png_pages.dll')==v['png_before_sha256']
  test=json.loads((OUT/'offline-verification.json').read_text());assert test['painted_pages']==1 and test['RGB_exact'] and not test['game_launched']
  assert not (RT/REL).exists()
  m=json.loads(MANIFEST.read_text(encoding='utf-8'));m['launcher_sha256']=b.sha(OUT/ENTRY.name);m['files']['png_pages.dll']=b.sha(OUT/'png_pages.dll');m['files'][REL]=b.sha(OUT/'ClosedBook.PNG');m['book_open_geometry']=v
  updates={ENTRY:(OUT/ENTRY.name).read_bytes(),RT/'png_pages.dll':(OUT/'png_pages.dll').read_bytes(),RT/REL:(OUT/'ClosedBook.PNG').read_bytes(),MANIFEST:(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()}
  BACK.mkdir(exist_ok=False);originals={p:p.read_bytes() if p.exists() else None for p in updates}
  rows=[]
  for p,raw in originals.items():
   rel=p.relative_to(b.ROOT).as_posix();rows.append(dict(path=rel,sha256=hashlib.sha256(updates[p]).hexdigest()))
   if raw is not None:target=BACK/'project'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  b.write(BACK/'installation.json',dict(files=rows))
  try:
   for p,raw in updates.items():replace(p,raw)
   b.verify()
  except BaseException:
   for p,raw in originals.items():
    if raw is None:p.unlink(missing_ok=True)
    else:replace(p,raw)
   raise
 print(action,'book opening passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);main(p.parse_args().action)
