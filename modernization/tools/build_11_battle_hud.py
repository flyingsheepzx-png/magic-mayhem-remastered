"""Current portable wrapper plus output-only HUD overlay, no gameplay launch."""
from pathlib import Path
import json,shutil,subprocess,argparse,hashlib
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from build_11_fmv_h264 import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-battle-hud'
BACK=b.ROOT/'modernization/backups/remastered-1.1-battle-hud'
ASSET=b.ROOT/'modernization/assets/hd/battle-hud-1.1'
OLD='8c46de4da7ca74b2a63ba5f3fcd6bc296b0646d26d0481b1587bc5074ee9eecb'

def build():
 OUT.mkdir(exist_ok=False);rows=[]
 source=b.ROOT/'modernization/build/remastered-1.1-portable-render/wrapper'
 assert b.sha(source/'bin/Release/ddraw.dll')==OLD
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and b.sha(e.parent/'runtime/ddraw.dll')==OLD
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 base.write(OUT/'before.json',rows)
 ws=OUT/'wrapper';shutil.copytree(source,ws,ignore=shutil.ignore_patterns('.git','bin','obj','Debug','Release','.vs'))
 for path in [b.SRC/'hud_overlay_core.h',b.ROOT/'modernization/wrapper-probe/mm_battle_hud.h']:shutil.copy2(path,ws/'src'/path.name)
 p=ws/'src/mm_mixed.h';s=p.read_text()
 s=b.replace_once(s,'IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)\n{','#include "mm_battle_hud.h"\n\nIDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)\n{')
 s=b.replace_once(s,'    mm_mixed_surface = *primary;','    mm_hud_present(primary,mm_mixed_pixels);\n    mm_mixed_surface = *primary;');p.write_text(s)
 subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
 print('Wrapper built; assets/core tests required before installation')

def install():
 base.idle();v=json.loads((OUT/'verification.json').read_text());pack=json.loads((ASSET/'pack.json').read_text())
 assert v['result']=='passed' and pack['portraits_complete']
 runtime_check=json.loads((OUT/'runtime-verification.json').read_text())
 assert runtime_check['result']=='passed' and runtime_check['wrapper_sha256']==v['wrapper_sha256'] and runtime_check['pack_sha256']==v['pack_sha256']
 dll=OUT/'wrapper/bin/Release/ddraw.dll';assert b.sha(dll)==v['wrapper_sha256']
 asset=ASSET/'battle-hud.bin';assert b.sha(asset)==pack['pack_sha256']==v['pack_sha256']
 BACK.mkdir(exist_ok=False);changes=[]
 for i,r in enumerate(json.loads((OUT/'before.json').read_text())):
  e,m=Path(r['entry']),Path(r['manifest']);assert b.sha(e)==r['entry_sha256'] and b.sha(m)==r['manifest_sha256']
  rt=e.parent/'runtime';manifest=json.loads(m.read_text(encoding='utf-8'));prefix='' if r['kind']=='candidate' else 'runtime/'
  manifest['files'][prefix+'ddraw.dll']=b.sha(dll);manifest['files'][prefix+'Sprites/battle-hud.bin']=b.sha(asset)
  manifest['battle_hud_hd']=dict(verification=v,runtime_verification=runtime_check,asset_plan=str(ASSET/'plan.json'),backup=str(BACK),runtime_acceptance='isolated save10 checks passed; pending user acceptance')
  for j,(p,data) in enumerate([(rt/'ddraw.dll',dll.read_bytes()),(rt/'Sprites/battle-hud.bin',asset.read_bytes()),(m,(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())]):
   old=b.sha(p) if p.exists() else None;bak=BACK/f'{i}-{j}.bak'
   if old:bak.write_bytes(p.read_bytes())
   changes.append(dict(path=str(p),backup=str(bak),before_sha256=old,after_sha256=hashlib.sha256(data).hexdigest(),data=data))
 base.write(BACK/'rollback.json',[{k:v for k,v in c.items() if k!='data'} for c in changes])
 try:
  for c in changes:replace(Path(c['path']),c['data']);assert b.sha(Path(c['path']))==c['after_sha256']
 except BaseException:
  for c in reversed(changes):
   p=Path(c['path'])
   if c['before_sha256']:replace(p,Path(c['backup']).read_bytes())
   elif p.exists():p.unlink()
  raise
 print('Installed output HUD HD with engine and embedded modules unchanged; user acceptance pending')

def rollback():
 base.idle();rows=json.loads((BACK/'rollback.json').read_text())
 for r in rows:assert b.sha(Path(r['path']))==r['after_sha256']
 for r in reversed(rows):
  p=Path(r['path'])
  if r['before_sha256']:
   assert b.sha(Path(r['backup']))==r['before_sha256'];replace(p,Path(r['backup']).read_bytes())
  else:
   assert p.resolve().is_relative_to(p.parent.resolve());p.unlink()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
