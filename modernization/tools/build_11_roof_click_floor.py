"""Conditional lower-floor fallback for fully obscured roof cells."""
import argparse,json,shutil,subprocess
import build_11_port_bindings_hd as prev
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-roof-click-floor'
BACK=b.ROOT/'modernization/backups/remastered-1.1-roof-click-floor'
SOURCE=prev.OUT
LATEST=SOURCE

def build():
 current=resources(base.DEST/base.ENTRY)
 assert current==resources(LATEST/'release.exe')
 assert current[102]==(SOURCE/'qol_bindings.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll'):shutil.copy2(p,OUT/p.name)
 for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'canopy_pick.inc',OUT/'canopy_pick.inc')
 base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()

def verify():
 current=resources(LATEST/'release.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  assert all(r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name!='canopy_pick.inc':assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name

def install():
 verify();v=json.loads((OUT/'verification.json').read_text())
 assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('roof_click_underlying_floor')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
