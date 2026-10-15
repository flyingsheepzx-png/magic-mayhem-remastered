"""Accept the owned save14 before/after telemetry, never player gameplay."""
import json
import build_11_dynamic_wait as b
def main():
 root=b.b.ROOT/'modernization/logs/remastered-ui'
 before=root/'save14-route-before-v1';after=root/'save14-route-after-v2'
 bs=json.loads((before/'samples.json').read_text());ss=json.loads((after/'samples.json').read_text())
 path=[]
 for x in ss:
  if not path or path[-1]!=x['grid']:path.append(x['grid'])
 assert path==[[18,44,6],[18,45,6],[18,46,6],[17,47,6],[18,48,6],[18,49,6],[18,50,6],[18,51,6],[18,52,6],[18,53,6]]
 assert ss[-1]['order']==1 and ss[-1]['motion']==0
 assert max(max(abs(a-c) for a,c in zip(x['world'],y['world'])) for x,y in zip(ss,ss[1:]))<=7
 for run in [before,after]:
  r=json.loads((run/'run/capture.json').read_text());assert r['restored'] and not r['cleanup_errors'] and not r['timed_out']
 identities=[json.loads((x/'capture.json').read_text()) for x in [before,after]]
 assert identities[0]['fixture_sha256']==identities[1]['fixture_sha256']
 assert identities[1]['identity']['launcher_sha256']==b.b.sha(b.OUT/'candidate.exe')
 v=json.loads((b.OUT/'verification.json').read_text());assert v['result']=='passed' and v['module_sha256']==b.b.sha(b.OUT/'repath.dll')
 v.update(save14_runtime_verified=True,runtime_path=path,before_arrival_seconds=bs[-1]['seconds'],after_arrival_seconds=ss[-1]['seconds'],runtime_evidence=str(after),installed_user_acceptance='pending',scope='stationary single-player width-one ordinary walking; complete local detours within16 edges/256 nodes, failed searches rate limited')
 b.base.write(b.OUT/'verification.json',v);print('Owned save14 dynamic-fire detour passed')
if __name__=='__main__':main()
