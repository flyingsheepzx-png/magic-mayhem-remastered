"""Hash-gated wrapped topology correction, preserving command response-v2."""
import argparse,json
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
base.OUT=base.b.ROOT/'modernization/build/remastered-1.1-wrap-route-v1'
base.BACK=base.b.ROOT/'modernization/backups/remastered-1.1-wrap-route-v1'
def install():
 reports=[json.loads((base.OUT/name).read_text()) for name in ('verification.json','wrap-verification.json','command-verification.json')]
 digest=base.b.sha(base.OUT/'repath.dll')
 assert all(r['result']=='passed' and r['module_sha256']==digest for r in reports)
 assert [r['checks'] for r in reports]==[37,24,43]
 for name in ('long_route.inc','command_response.inc'):assert (base.OUT/name).read_bytes()==(base.b.SRC/name).read_bytes()
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'));assert base.b.sha(e)==manifest['launcher_sha256']
  assert base.b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  old=resources(e);new=resources(base.OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
  assert set(old)==set(new) and new[101]==(base.OUT/'repath.dll').read_bytes() and all(old[i]==new[i] for i in old if i!=101)
 result=dict(result='passed',checks=104,module_sha256=digest,wrapped_route=reports[1],command_response=reports[2],runtime_acceptance='pending user save20 testing')
 base.write(base.OUT/'verification.json',result);base.install('save20_wrapped_route')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);a=p.parse_args()
 if a.action=='install':install()
 else:base.rollback()
