"""Approved English setting labels avoid ambiguous legacy Chinese glyphs."""
import json,re,hashlib
from pathlib import Path
import build_11_surface_lifecycle as base
import install_options_resolution as i
BACK=base.b.ROOT/'modernization/backups/remastered-1.1-options-english-v1'
def labels(raw):
 for k,value in [(19,b'Render FPS'),(20,b'Game speed'),(95,b'Fast 40 logic FPS'),(96,b'Medium 30 logic FPS'),(97,b'Slow 20 logic FPS')]:
  raw,n=re.subn(rb'(?m)^(STR_'+str(k).encode()+rb'\s*=\s*)[^\r\n]*',lambda m:m[1]+value,raw);assert n==1
 return raw
def main():
 base.idle();changes=[]
 for n,(e,m,k) in enumerate(base.targets()):
  d=json.loads(m.read_text(encoding='utf-8'));assert base.b.sha(e)==d['launcher_sha256']
  path=e.parent/'runtime/CFG/interface screens text.cfg';before=path.read_bytes();after=labels(before)
  prefix='' if k=='candidate' else 'runtime/';d['files'][prefix+'CFG/interface screens text.cfg']=hashlib.sha256(after).hexdigest();d['options_english_labels']={'reason':'user approved English to avoid legacy glyph ambiguity','strings':['Render FPS','Game speed','Fast 40 logic FPS','Medium 30 logic FPS','Slow 20 logic FPS']}
  for j,(p,data) in enumerate([(path,after),(m,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())]):
   changes.append(dict(path=str(p),backup=str(BACK/f'{n}-{j}.bak'),before_sha256=base.b.sha(p),after_sha256=hashlib.sha256(data).hexdigest(),data=data))
 BACK.mkdir(exist_ok=False)
 for r in changes:Path(r['backup']).write_bytes(Path(r['path']).read_bytes())
 base.write(BACK/'rollback.json',[{k:v for k,v in r.items() if k!='data'} for r in changes])
 try:
  for r in changes:i.replace(Path(r['path']),r['data']);assert base.b.sha(Path(r['path']))==r['after_sha256']
 except BaseException:
  for r in changes:i.replace(Path(r['path']),Path(r['backup']).read_bytes())
  raise
 print('English labels installed, unrelated bytes unchanged')
if __name__=='__main__':main()
