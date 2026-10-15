"""Save21 native roof-group correction, preserving all installed modules."""
import argparse,json,shutil,subprocess
import build_11_roof_ghost as prev
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-roof-ghost-v2'
BACK=b.ROOT/'modernization/backups/remastered-1.1-roof-ghost-v2'
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(prev.OUT/'release.exe')
 for e,m,k in base.targets():
  assert resources(e)==current and b.sha(e)==json.loads(m.read_text(encoding='utf-8'))['launcher_sha256']
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 OUT.mkdir(exist_ok=False)
 for p in prev.OUT.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.dll'):shutil.copy2(p,OUT/p.name)
 shutil.copy2(b.SRC/'roof_ghost.inc',OUT/'roof_ghost.inc')
 base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
def install():
 reports=[json.loads((OUT/n).read_text()) for n in ('ghost-verification.json','wrap-verification.json','command-verification.json','verification.json')]
 assert all(v['result']=='passed' and v['module_sha256']==b.sha(OUT/'repath.dll') for v in reports)
 acceptance=json.loads((OUT/'runtime-acceptance.json').read_text());assert acceptance['result']=='passed' and acceptance['module_sha256']==b.sha(OUT/'repath.dll')
 assert (OUT/'roof_ghost.inc').read_bytes()==(b.SRC/'roof_ghost.inc').read_bytes()
 current=resources(prev.OUT/'release.exe')
 for n in ('candidate.exe','release.exe'):
  r=resources(OUT/n);assert set(r)==set(current) and all(r[i]==((OUT/'repath.dll').read_bytes() if i==101 else current[i]) for i in current)
 base.write(OUT/'verification.json',dict(result='passed',checks=sum(v['checks'] for v in reports),module_sha256=b.sha(OUT/'repath.dll'),reports=reports,runtime_acceptance=acceptance))
 base.OUT=OUT;base.BACK=BACK;base.install('roof_group_unit_ghost_v2')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
