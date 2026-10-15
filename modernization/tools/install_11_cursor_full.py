"""Install only full-primary software-cursor backing and clip bounds."""
import json
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources,replace
FIX=b.ROOT/'modernization/build/remastered-1.1-cursor-full'
BACK=b.ROOT/'modernization/backups/remastered-1.1-cursor-full'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
MANIFEST=b.TARGET/'manifest.json'

def install():
 idle();b.verify();old=json.loads(MANIFEST.read_text(encoding='utf-8'))
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 assert b.sha(ENTRY)==old['launcher_sha256']
 current=resources(ENTRY);new=resources(FIX/ENTRY.name)
 import hashlib
 assert hashlib.sha256(current[102]).hexdigest()=='0ece558e969d36299f46bbfbd344c6ae1997987e804c67e558cefe4d0ba8a01b'
 assert current[101]==new[101] and new[102]==(FIX/'qol_bindings.dll').read_bytes()
 BACK.mkdir(exist_ok=False)
 for p in (ENTRY,MANIFEST):(BACK/p.name).write_bytes(p.read_bytes())
 old['launcher_sha256']=b.sha(FIX/ENTRY.name)
 old['cursor_full_primary']=dict(module_sha256=b.sha(FIX/'qol_bindings.dll'),backing=[2560,1440],battle_input=[1280,720],backup=str(BACK),acceptance='compiled/hash verified; pending user testing')
 try:
  replace(ENTRY,(FIX/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(old,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));b.verify()
 except BaseException:
  for p in (ENTRY,MANIFEST):replace(p,(BACK/p.name).read_bytes())
  raise
 print('Installed full-primary cursor; battle coordinate transform unchanged')

def rollback():
 idle();m=json.loads(MANIFEST.read_text(encoding='utf-8'))
 assert m['cursor_full_primary']['module_sha256']==__import__('hashlib').sha256(resources(ENTRY)[102]).hexdigest()
 for p in (ENTRY,MANIFEST):replace(p,(BACK/p.name).read_bytes())
 b.verify()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);globals()[p.parse_args().action]()
