"""Normalize paired stat-bar artwork to authoritative native UI Rect2 extents."""
from pathlib import Path
import argparse,json,re,hashlib
import numpy as np
from PIL import Image
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from build_11_fmv_h264 import replace
import seedvr_ui_11 as sr
OUT=b.ROOT/'modernization/build/remastered-1.1-stat-preview'
BACK=b.ROOT/'modernization/backups/remastered-1.1-stat-preview'
REL=Path('Interface/CharacterScreen')

def build():
 OUT.mkdir(exist_ok=False);assets=OUT/'assets';assets.mkdir();records=[];targets=[]
 cfg=base.DEST/'runtime'/REL/'screen (Character Screen).cfg'
 data=cfg.read_text(encoding='gb18030');sections=re.findall(r'\[STATBAR_\d+\]([^\[]+)',data);assert len(sections)==3
 for block in sections:
  rect=list(map(int,re.search(r'Rect2\s*=\s*([\d,]+)',block)[1].split(',')));size=(rect[2]-rect[0],rect[3]-rect[1]);assert all(0<s<=4096 for s in size)
  name=Path(re.search(r'Text\s*=\s*([^;]+)',block)[1].strip()).with_suffix('.PNG').name
  source=base.DEST/'runtime'/REL/'800x600'/name;old=Image.open(source).convert('RGB');assert old.size==(1400,40)
  # Resize each state independently: no filter samples cross colour/gray seam.
  result=Image.new('RGB',(size[0]*2,size[1]))
  for state in range(2):
   part=old.crop((state*700,0,(state+1)*700,40));scaled=part.resize(size,Image.Resampling.LANCZOS)
   baseline=part.resize(size,Image.Resampling.NEAREST);mask=sr.keys(baseline);pixels=np.array(scaled);nearest=np.array(baseline)
   pixels[mask]=nearest[mask];extra=sr.keys(Image.fromarray(pixels))&~mask;pixels[extra]=nearest[extra]
   fixed=Image.fromarray(pixels);assert np.array_equal(sr.keys(fixed),mask);result.paste(fixed,(state*size[0],0))
  destination=assets/name;result.save(destination)
  records.append(dict(path=(REL/'800x600'/name).as_posix(),source_sha256=b.sha(source),output_sha256=b.sha(destination),before=list(old.size),after=list(result.size),state_size=list(size),rect=rect))
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==manifest['launcher_sha256']
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  assert b.sha(e.parent/'runtime'/REL/cfg.name)==b.sha(cfg)
  for row in records:assert b.sha(e.parent/'runtime'/row['path'])==row['source_sha256']
  targets.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 # All legal old/new value pairs must keep their source rectangle in its state.
 cases=0
 for maximum in [200,800,40]:
  for value in range(maximum+1):
   for preview in range(value,maximum+1):
    start=value*840//maximum;end=preview*840//maximum
    assert 0<=start<=end<=840 and 840+end<=1680;cases+=1
 b.write(OUT/'verification.json',dict(result='passed',source_cfg_sha256=b.sha(cfg),assets=records,source_rect_cases=cases,save12_verified=False,scope='paired colour/preview atlas size follows Rect2; no engine or gameplay changes'))
 b.write(OUT/'before.json',targets);print(cases,'source rectangles passed')

def install():
 base.idle();v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['save12_verified'];changes=[]
 for i,row in enumerate(json.loads((OUT/'before.json').read_text())):
  e,m=Path(row['entry']),Path(row['manifest']);assert b.sha(e)==row['entry_sha256'] and b.sha(m)==row['manifest_sha256'];manifest=json.loads(m.read_text(encoding='utf-8'));prefix='' if row['kind']=='candidate' else 'runtime/'
  for j,asset in enumerate(v['assets']):
   p=e.parent/'runtime'/asset['path'];new=OUT/'assets'/p.name;assert b.sha(p)==asset['source_sha256'] and b.sha(new)==asset['output_sha256'];manifest['files'][prefix+asset['path']]=asset['output_sha256']
   changes.append(dict(path=str(p),backup=str(BACK/f'{i}-{j}.bak'),before_sha256=b.sha(p),after_sha256=b.sha(new),data=new.read_bytes()))
  manifest['stat_preview_fix']=v;data=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();changes.append(dict(path=str(m),backup=str(BACK/f'{i}-manifest.bak'),before_sha256=b.sha(m),after_sha256=hashlib.sha256(data).hexdigest(),data=data))
 BACK.mkdir(exist_ok=False)
 for row in changes:Path(row['backup']).write_bytes(Path(row['path']).read_bytes())
 b.write(BACK/'rollback.json',[{k:v for k,v in row.items() if k!='data'} for row in changes])
 try:
  for row in changes:replace(Path(row['path']),row['data']);assert b.sha(Path(row['path']))==row['after_sha256']
 except BaseException:
  for row in reversed(changes):replace(Path(row['path']),Path(row['backup']).read_bytes())
  raise
 print('Installed normalized stat preview artwork; user acceptance pending')

def rollback():
 base.idle();rows=json.loads((BACK/'rollback.json').read_text())
 for r in rows:assert b.sha(Path(r['path']))==r['after_sha256'] and b.sha(Path(r['backup']))==r['before_sha256']
 for r in reversed(rows):replace(Path(r['path']),Path(r['backup']).read_bytes())

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
