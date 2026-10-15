"""Atomic first settings iteration, with exact current identity and rollback."""
import argparse,json,hashlib
from pathlib import Path
import prepare_options_resolution as prep
from build_11_fmv_h264 import replace as atomic_replace
OUT=prep.OUT;BACK=prep.b.ROOT/'modernization/backups/remastered-1.1-options-resolution-v2'
MANIFEST_FIELD='options_resolution'
EXTRA_RUNTIME_CHANGES=()
def replace(path,data):
 import time
 for attempt in range(5):
  try:return atomic_replace(path,data)
  except OSError:
   if attempt==4:
    print('Replacement failed:',path,flush=True);raise
   time.sleep(.3)
def label_bytes(raw):
 import re
 for key,value in [(22,b'2560x1440'),(23,b'1920x1080')]:
  pattern=rb'(?m)^(STR_'+str(key).encode()+rb'\s*=\s*)[^\r\n]*'
  raw,n=re.subn(pattern,lambda m:m[1]+value,raw);assert n==1
 return raw
def install():
 prep.base.idle();v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed'
 assert v['module_sha256']==prep.b.sha(OUT/'qol_bindings.dll') and v['wrapper_sha256']==prep.b.sha(OUT/'wrapper/bin/Release/ddraw.dll')
 rows=json.loads((OUT/'before.json').read_text());changes=[]
 for i,r in enumerate(rows):
  e,m=Path(r['entry']),Path(r['manifest']);rt=e.parent/'runtime'
  assert prep.b.sha(e)==r['entry_sha256'] and prep.b.sha(m)==r['manifest_sha256'] and prep.b.sha(rt/'ddraw.dll')==r['wrapper_sha256']
  d=json.loads(m.read_text(encoding='utf-8'));prefix='' if r['kind']=='candidate' else 'runtime/'
  new=OUT/('candidate.exe' if r['kind']=='candidate' else 'release.exe');d['launcher_sha256']=prep.b.sha(new)
  d[MANIFEST_FIELD]=v
  if r['kind']=='release':d['files'][e.name]=prep.b.sha(new);d['embedded_modules']['102']=v['module_sha256']
  text=rt/'CFG/interface screens text.cfg';textdata=label_bytes(text.read_bytes())
  wrapperdata=(OUT/'wrapper/bin/Release/ddraw.dll').read_bytes()
  d['files'][prefix+'ddraw.dll']=v['wrapper_sha256'];d['files'][prefix+'CFG/interface screens text.cfg']=hashlib.sha256(textdata).hexdigest()
  extra=[]
  for name,transform in EXTRA_RUNTIME_CHANGES:
   path=rt/name;data=transform(path.read_bytes());extra.append((path,data))
   d['files'][prefix+name]=hashlib.sha256(data).hexdigest()
  for j,(path,data) in enumerate([(e,new.read_bytes()),(rt/'ddraw.dll',wrapperdata),(text,textdata),(m,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()),*extra]):
   changes.append(dict(path=str(path),backup=str(BACK/f'{i}-{j}.bak'),before_sha256=prep.b.sha(path),after_sha256=hashlib.sha256(data).hexdigest(),data=data))
 BACK.mkdir(exist_ok=False)
 for r in changes:Path(r['backup']).write_bytes(Path(r['path']).read_bytes())
 prep.base.write(BACK/'rollback.json',[{k:v for k,v in r.items() if k!='data'} for r in changes])
 try:
  for r in changes:replace(Path(r['path']),r['data']);assert prep.b.sha(Path(r['path']))==r['after_sha256']
 except BaseException:
  for r in changes:replace(Path(r['path']),Path(r['backup']).read_bytes())
  raise
 print('Resolution settings installed; player runtime acceptance pending')
def rollback():
 prep.base.idle();rows=json.loads((BACK/'rollback.json').read_text())
 for r in rows:assert prep.b.sha(Path(r['path']))==r['after_sha256'] and prep.b.sha(Path(r['backup']))==r['before_sha256']
 for r in rows:replace(Path(r['path']),Path(r['backup']).read_bytes())
 print('Resolution iteration rolled back')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);globals()[p.parse_args().action]()
