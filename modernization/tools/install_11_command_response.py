"""Install/rollback symmetric command redirection with current-hash gates."""
import argparse,json
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
base.OUT=base.b.ROOT/'modernization/build/remastered-1.1-command-response-v1'
base.BACK=base.b.ROOT/'modernization/backups/remastered-1.1-command-response-v1'
def install():
 v=json.loads((base.OUT/'verification.json').read_text())
 cmd=json.loads((base.OUT/'command-verification.json').read_text())
 digest=base.b.sha(base.OUT/'repath.dll')
 assert v['result']==cmd['result']=='passed' and v['checks']==37 and cmd['checks'] in (38,43)
 assert v['module_sha256']==cmd['module_sha256']==digest
 assert (base.OUT/'command_response.inc').read_bytes()==(base.b.SRC/'command_response.inc').read_bytes()
 for entry,manifest,kind in base.targets():
  m=json.loads(manifest.read_text(encoding='utf-8'));assert base.b.sha(entry)==m['launcher_sha256']
  assert base.b.sha(entry.parent/'runtime/Chaos-Wide169-engine.exe')==m['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  current=resources(entry);new=resources(base.OUT/('candidate.exe' if kind=='candidate' else 'release.exe'))
  assert set(current)==set(new) and new[101]==(base.OUT/'repath.dll').read_bytes()
  assert all(new[i]==current[i] for i in current if i!=101)
 v.update(command_response=cmd,checks=37+cmd['checks'],army_policy='symmetric single-player player/AI ordinary walker safety rules; no owner/selection/caller privilege',runtime_acceptance='pending user save18 testing')
 base.write(base.OUT/'verification.json',v)
 base.install('symmetric_command_response')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);a=p.parse_args()
 if a.action=='install':install()
 else:base.rollback()
