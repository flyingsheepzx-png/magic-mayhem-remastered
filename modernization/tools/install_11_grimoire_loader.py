"""Repair Grimoire loader coverage and page content/canvas distinction."""
import argparse,json,shutil,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
import seedvr_ui_11 as s
from install_11_minimap_v2 import resources
b=s.b
FIX=b.ROOT/'modernization/build/remastered-1.1-grimoire-load'
BACK=b.ROOT/'modernization/backups/remastered-1.1-grimoire-load'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
MANIFEST=b.TARGET/'manifest.json'

def prepare():
 plan=json.loads(s.PLAN.read_text(encoding='utf-8'));tasks={t['id']:t for t in plan['tasks']};rows=[]
 for a in plan['assets']:
  if a['type']!='raster' or 'Grimoire/800x600/' not in a['path'] or not a['path'].endswith('.PNG'):continue
  assert a['size']==[1280,1440]
  task=tasks[a['task']];assert s.sha(Path(task['output']))==task['output_sha256']
  source=Image.open(task['output']).convert('RGB').resize((960,1440),Image.Resampling.LANCZOS)
  left=Path(a['path']).name.startswith('GenericL') or 'P1_' in a['path']
  result=Image.new('RGB',(1280,1440),(0,0,255));result.paste(source,(320 if left else 0,0))
  baseline=Image.open(s.BACK/'runtime'/a['path']).convert('RGB');mask=s.keys(baseline);pixels=np.array(result);old=np.array(baseline)
  pixels[mask]=old[mask];extra=s.keys(Image.fromarray(pixels))&~mask;pixels[extra]=old[extra]
  result=Image.fromarray(pixels);assert np.array_equal(s.keys(result),mask)
  output=FIX/'runtime'/a['path'];output.parent.mkdir(parents=True,exist_ok=True);result.save(output)
  rows.append(dict(path=a['path'],before_sha256=a['sha256'],sha256=s.sha(output),content=[960,1440],canvas=[1280,1440],origin=[320 if left else 0,0]))
 assert len(rows)==190
 # Native backdrop uses BMP-first with JPEG fallback; supply a lossless sibling.
 a=next(a for a in plan['assets'] if a['path']=='Interface/Grimoire/800x600/Backdrop.JPG')
 source=Path(a['output']).with_suffix('.PNG');target=FIX/'runtime/Interface/Grimoire/800x600/Backdrop.PNG'
 shutil.copy2(source,target);rows.append(dict(path=target.relative_to(FIX/'runtime').as_posix(),before_sha256=None,sha256=s.sha(target)))
 b.write(FIX/'asset-fix.json',dict(rows=rows,scope='190pages content geometry and PNG-first backdrop'))
 # Reuse real WIC/GDI/fastcall tests at new native geometry; all three suffixes.
 test=(b.ROOT/'modernization/runtime/png-pages/offline_test.cpp').read_text(encoding='utf-8')
 test=test.replace('w!=640 || h!=720','w!=1280 || h!=1440')
 test=test.replace('GdiFlush();int stride=', '''for(const char* suffix:{".PNG",".JPG"}){
   std::string path(filename);path.replace(path.size()-4,4,suffix);
   if(page(image,nullptr,path.c_str())!=1)return 18;
  }
  GdiFlush();int stride=''')
 (FIX/'offline_test.cpp').write_text(test,encoding='utf-8')
 fixture=FIX/'offline-bmp';fixture.mkdir(exist_ok=False)
 for r in rows[:190]:Image.open(FIX/'runtime'/r['path']).save(fixture/Path(r['path']).with_suffix('.BMP').name)
 cmd='@echo off\ncall "'+str(b.VC)+'" x86 >nul\ncl /nologo /MT /O2 /EHsc /std:c++17 /W4 offline_test.cpp /link /OUT:offline_test.exe gdi32.lib user32.lib\n'
 (FIX/'build-test.cmd').write_text(cmd,encoding='ascii');subprocess.run(['cmd','/c','build-test.cmd'],cwd=FIX,check=True)
 pngfixture=FIX/'offline-png';pngfixture.mkdir(exist_ok=False)
 for r in rows[:190]:shutil.copy2(FIX/'runtime'/r['path'],pngfixture/Path(r['path']).name)
 result=subprocess.run([str(FIX/'offline_test.exe'),str(FIX/'png_pages_test.dll'),str(pngfixture),str(fixture)],check=True,capture_output=True,text=True)
 b.write(FIX/'offline-verification.json',json.loads(result.stdout));print(result.stdout)

def install():
 s.idle();b.verify();m=json.loads(MANIFEST.read_text(encoding='utf-8'));plan=json.loads(s.PLAN.read_text(encoding='utf-8'))
 assert s.sha(s.RT/'Chaos-Wide169-engine.exe')==plan['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 assert s.sha(ENTRY)==m['launcher_sha256'] and s.sha(s.RT/'png_pages.dll')=='bc03168bd19a3e6e376f06a79d6e9fa8fcff3f896c6c23bf0ad60251cb2c9bd7'
 assert resources(ENTRY)==resources(FIX/ENTRY.name)
 assert json.loads((FIX/'offline-verification.json').read_text())['painted_pages']==190
 rows=json.loads((FIX/'asset-fix.json').read_text())['rows'];updates={ENTRY:(FIX/ENTRY.name).read_bytes(),s.RT/'png_pages.dll':(FIX/'png_pages.dll').read_bytes()}
 for r in rows:
  target=s.RT/r['path'];assert (s.sha(target) if target.exists() else None)==r['before_sha256']
  updates[target]=(FIX/'runtime'/r['path']).read_bytes();assert s.sha(FIX/'runtime'/r['path'])==r['sha256']
 originals={p:p.read_bytes() if p.exists() else None for p in [*updates,MANIFEST]}
 BACK.mkdir(exist_ok=False)
 (BACK/'production-plan.json').write_bytes(s.PLAN.read_bytes())
 for p,raw in originals.items():
  if raw is not None:
   out=BACK/p.relative_to(b.TARGET);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
 m['launcher_sha256']=s.sha(FIX/ENTRY.name);m['files']['png_pages.dll']=s.sha(FIX/'png_pages.dll')
 for r in rows:m['files'][r['path']]=r['sha256']
 m['grimoire_loader_geometry_fix']=dict(backup=str(BACK),pages=190,content=[960,1440],page_canvas=[1280,1440],loader_calls=['4c532f','4c5380','4c574c','4c575c'],acceptance='190 native WIC/GDI pages and BMP/PNG/JPG call aliases passed offline; pending user playtest')
 updates[MANIFEST]=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 try:
  for p,raw in updates.items():s.replace(p,raw)
  b.verify()
 except BaseException:
  for p,raw in originals.items():
   if raw is None:p.unlink(missing_ok=True)
   else:s.replace(p,raw)
  raise
 # Keep the production recipe aligned with revised page geometry.
 for r in rows[:190]:
  a=next(a for a in plan['assets'] if a['path']==r['path']);s.replace(Path(a['output']),updates[s.RT/r['path']]);a.update(sha256=r['sha256'],content_size=[960,1440],page_origin=r['origin'],grimoire_geometry_fixed=True)
 s.save(s.PLAN,plan)
 b.write(BACK/'installation.json',dict(files={str(p.relative_to(b.TARGET)):s.sha(p) for p in updates},added=[str(p.relative_to(b.TARGET)) for p,v in originals.items() if v is None],runtime_pending_user=True))
 print('Installed190page geometry and complete Grimoire PNG loading; preserved cursor fix')

def rollback():
 s.idle();state=json.loads((BACK/'installation.json').read_text());
 for n,h in state['files'].items():assert s.sha(b.TARGET/n)==h
 for n in state['files']:
  p=b.TARGET/n
  if n in state['added']:p.unlink()
  else:s.replace(p,(BACK/n).read_bytes())
 if (BACK/'production-plan.json').exists():
  plan=json.loads((BACK/'production-plan.json').read_text(encoding='utf-8'))
  for a in plan['assets']:
   n='runtime/'+a['path']
   if n in state['files'] and (BACK/n).exists():s.replace(Path(a['output']),(BACK/n).read_bytes())
  s.save(s.PLAN,plan)
 b.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','install','rollback']);globals()[p.parse_args().action]()
