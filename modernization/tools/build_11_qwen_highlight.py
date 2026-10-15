"""Derive all region states from approved maps and original keyed masks."""
import argparse,json,shutil,subprocess,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
from realm_portal_art import PORTALS, composite_portal
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources
from build_11_campaign_ui import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-qwen-highlight';BACK=b.ROOT/'modernization/backups/remastered-1.1-qwen-highlight'
RT=b.TARGET/'runtime';ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'
def run(action):
 if action=='rollback':
  idle();state=json.loads((BACK/'installation.json').read_text())
  for row in state['files']:assert b.sha(b.ROOT/row['path'])==row['sha256']
  for row in state['files']:
   p=b.ROOT/row['path'];old=BACK/'project'/row['path']
   if old.exists():replace(p,old.read_bytes())
   else:p.unlink()
  b.verify();return
 b.verify();assert b.sha(RT/'Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 if action=='build':
  OUT.mkdir(exist_ok=True);source=b.ROOT/'modernization/build/remastered-1.1-confirm-dialog'
  assert resources(ENTRY)[102]==(source/'qol_bindings.dll').read_bytes()
  for n in ['qol_bindings.cpp','mixed_ui_fonts.cpp','campaign_ui.cpp','port_drag.cpp','confirm_dialog.cpp','layout_context.h','ui_geometry.h','repath.dll','combined.rc','launcher.cpp']:shutil.copy2(source/n,OUT/n)
  shutil.copy2(b.SRC/'qwen_highlight.cpp',OUT/'qwen_highlight.cpp')
  q=(OUT/'qol_bindings.cpp').read_text()
  q=q.replace('unsigned realm_highlight_region=0;','unsigned realm_highlight_region=0;\nunsigned char* realm_highlight_owner=nullptr;\nextern "C" int mm_qwen_highlight(void*,RECT*,const char*,unsigned);')
  q=q.replace('mov dword ptr [realm_highlight_region],edi','mov dword ptr [realm_highlight_region],edi\n    mov dword ptr [realm_highlight_owner],esi')
  needle='    auto* src=*reinterpret_cast<void**>(static_cast<unsigned char*>(source)+8);';assert q.count(needle)==1
  q=q.replace(needle,'    if(realm_highlight_owner && mm_qwen_highlight(destination,&target,*(const char**)(realm_highlight_owner+0x12),realm_highlight_region))return 1;\n'+needle)
  (OUT/'qol_bindings.cpp').write_text(q)
  cmd=(source/'build.cmd').read_text().replace('confirm_dialog.cpp /link','confirm_dialog.cpp qwen_highlight.cpp /link');(OUT/'build.cmd').write_text(cmd)
  subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);assert resources(ENTRY)[101]==resources(OUT/ENTRY.name)[101]
  records=[];maps={}
  for world in ['Celtic','Greek','Medieval']:
   base=RT/f'Interface/RealmViewer/800x600/{world}_Map.PNG';maps[world]=b.sha(base)
   approved=b.ROOT/f'modernization/assets/hd/seedvr2-ui-1.1/approved-qwen-maps/{world}_Map.PNG';assert b.sha(base)==b.sha(approved)
   rgb=np.array(Image.open(base).convert('RGB'));assert rgb.shape==(1440,2560,3)
   masks=sorted((RT/'Interface/RealmViewer/800x600').glob(world+'_*'))
   masks=[p for p in masks if '_border_' in p.name.lower() and p.suffix.lower()=='.pcx']
   for source in masks:
    region=int(source.stem.split('_')[-1]);old=Image.open(source).convert('RGB');assert old.size==(800,600)
    pixels=np.array(old);mask=np.any(pixels!=[0,0,255],axis=2)
    # Supersample the original outline. Blend onto the SAME base map, never blue.
    m=Image.fromarray((mask*255).astype('uint8')).resize((1920,1440),Image.Resampling.LANCZOS)
    coverage=Image.new('L',(2560,1440));coverage.paste(m,(320,0));a=np.array(coverage,dtype=np.float32)/255
    eroded=m.filter(ImageFilter.MinFilter(9));rim=Image.new('L',(2560,1440));rim.paste(eroded,(320,0));edge=np.clip(a-np.array(rim,dtype=np.float32)/255,0,1)
    colour=rgb.astype(np.float32);enhanced=np.minimum(colour*1.10+np.array([3,4,0]),255)
    result=colour+(enhanced-colour)*a[:,:,None]
    # Native yellow-green outline, smoothly confined to the original silhouette.
    result=result*(1-edge[:,:,None]*.6)+np.array([208,220,55])*edge[:,:,None]*.6
    result=np.rint(result).clip(0,255).astype('uint8');assert np.array_equal(result[a==0],rgb[a==0])
    # Chapter transitions carry authored vortex art, not selected terrain.
    if (world,region) in PORTALS:
     portal,coverage=composite_portal(Image.fromarray(rgb),old)
     result=np.array(portal);outside=np.array(coverage)==0
     assert np.array_equal(result[outside],rgb[outside])
    rel=f'Interface/RealmViewer/hd-selected/{world}_{region:02d}.PNG';output=OUT/'runtime'/rel;output.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(result).save(output)
    records.append(dict(path=rel,sha256=b.sha(output),mask_sha256=b.sha(source),mask_path=source.relative_to(RT).as_posix(),outside_exact=True,region=region,world=world))
  assert len(records)==41
  b.write(OUT/'verification.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST),maps=maps,records=records,art='approved Qwen pixels + original PCX coverage, deterministic tint and inward rim',regions=len(records)))
 else:
  idle();v=json.loads((OUT/'verification.json').read_text());assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  m=json.loads(MANIFEST.read_text(encoding='utf-8'));updates={ENTRY:(OUT/ENTRY.name).read_bytes()}
  for r in v['records']:
   p=RT/r['path'];assert not p.exists();assert b.sha(OUT/'runtime'/r['path'])==r['sha256'];assert b.sha(RT/r['mask_path'])==r['mask_sha256']
   updates[p]=(OUT/'runtime'/r['path']).read_bytes();m['files'][r['path']]=r['sha256']
  for world,digest in v['maps'].items():assert b.sha(RT/f'Interface/RealmViewer/800x600/{world}_Map.PNG')==digest
  m['launcher_sha256']=b.sha(OUT/ENTRY.name);m['qwen_region_highlights']=v
  updates[MANIFEST]=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode();BACK.mkdir(exist_ok=False)
  before={p:p.read_bytes() if p.exists() else None for p in updates};rows=[]
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
 print(action,'Qwen region states passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
