"""Two native scanner marker anchor deltas on exact installed1.1 module."""
import argparse,shutil,json,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-minimap-units'
BACK=b.ROOT/'modernization/backups/remastered-1.1-minimap-units'

def build():
 source=b.ROOT/'modernization/build/remastered-1.1-minimap-release';launch=b.ROOT/'modernization/build/remastered-1.1-half-stair';OUT.mkdir(exist_ok=False)
 current=resources(base.DEST/base.ENTRY);assert current==resources(launch/'candidate.exe')
 assert current[102]==(source/'qol_bindings.dll').read_bytes()
 for p in source.iterdir():
  if p.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico'] or p.name in ['repath.dll','ai_diagnostics.dll']:shutil.copy2(p,OUT/p.name)
 for name in ['launcher.cpp','release_launcher.cpp']:shutil.copy2(launch/name,OUT/name)
 shutil.copy2(b.SRC/'mixed_ui_fonts.cpp',OUT/'mixed_ui_fonts.cpp')
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 b.write(OUT/'before.json',rows);subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert r[101]==current[101] and r[103]==current[103] and r[102]==(OUT/'qol_bindings.dll').read_bytes()

def install():
 v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['save14_verified'] and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('minimap_unit_marker_fix')

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
