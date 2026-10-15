"""Stage/install the isolated 1.1 wrapper close policy; preserve engine/modules."""
import argparse,json,re
import build_remastered_11 as b
from install_11_minimap_v2 import idle,replace
OUT=b.ROOT/'modernization/build/remastered-1.1-wrapper-close'
BACK=b.ROOT/'modernization/backups/remastered-1.1-wrapper-close'
INI=b.TARGET/'runtime/ddraw.ini'
MANIFEST=b.TARGET/'manifest.json'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'

def run(action):
 if action=='rollback':
  idle();v=json.loads((BACK/'installation.json').read_text())
  assert b.sha(INI)==v['ini_sha256'] and b.sha(MANIFEST)==v['manifest_sha256']
  for p in [INI,MANIFEST]:replace(p,(BACK/p.name).read_bytes())
  b.verify();print('Restored preceding wrapper close configuration');return
 b.verify()
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 assert b.sha(ENTRY)=='a9d8be74de5972f66cce989871f3abf9ca6472e68f9254fa7f7f8d8be6b6c292'
 if action=='build':
  raw=INI.read_bytes()
  # Only the global default changes. The runtime executable has no override.
  assert not re.search(rb'(?im)^\[Chaos-Wide169-engine\]',raw)
  first_section_end=raw.find(b'\n[',raw.index(b'[ddraw]')+7)
  assert first_section_end>0
  prefix,n=re.subn(rb'(?m)^game_handles_close=false(?=\r?$)',b'game_handles_close=true',raw[:first_section_end])
  assert n==1
  OUT.mkdir(exist_ok=False);(OUT/'ddraw.ini').write_bytes(prefix+raw[first_section_end:])
  evidence=b.ROOT/'modernization/logs/remastered-ui'
  states={n:json.loads((evidence/n/'exit-state.json').read_text()) for n in ['exit-system-before-v2','exit-system-game-close-v1','exit-altf4-game-close-v1']}
  assert not states['exit-system-before-v2']['exited']
  for n in ['exit-system-game-close-v1','exit-altf4-game-close-v1']:
   assert states[n]['exited'] and states[n]['launcher_exited']
   assert states[n]['observed_seconds']<2
   capture=json.loads((evidence/n/'1.1/capture.json').read_text())
   assert capture['restored'] and not capture['cleanup_errors']
  b.write(OUT/'build-state.json',dict(ini_before_sha256=b.sha(INI),manifest_before_sha256=b.sha(MANIFEST),launcher_sha256=b.sha(ENTRY),wrapper_sha256=b.sha(b.TARGET/'runtime/ddraw.dll'),ini_sha256=b.sha(OUT/'ddraw.ini'),evidence=states,acceptance='owned menu close diagnostics passed; battle/user exit acceptance pending'))
 else:
  idle();v=json.loads((OUT/'build-state.json').read_text())
  assert b.sha(INI)==v['ini_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  assert b.sha(OUT/'ddraw.ini')==v['ini_sha256']
  assert b.sha(b.TARGET/'runtime/ddraw.dll')==v['wrapper_sha256']
  BACK.mkdir(exist_ok=False);before={p:p.read_bytes() for p in [INI,MANIFEST]}
  for p,raw in before.items():(BACK/p.name).write_bytes(raw)
  inventory=b.inventory(b.TARGET/'runtime');m=json.loads(before[MANIFEST])
  m['files']['ddraw.ini']=v['ini_sha256']
  m['wrapper_close_policy']=dict(game_handles_close=True,backup=str(BACK),verification=v)
  m['window_close_fix']['user_feedback']='first engine-only correction did not resolve Alt+F4; wrapper close policy supplements it'
  try:
   replace(INI,(OUT/'ddraw.ini').read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode())
   after=b.inventory(b.TARGET/'runtime');inventory['ddraw.ini']=v['ini_sha256'];assert after==inventory
   assert b.sha(ENTRY)==v['launcher_sha256'];b.verify()
  except BaseException:
   for p,raw in before.items():replace(p,raw)
   raise
  b.write(BACK/'installation.json',dict(ini_sha256=b.sha(INI),manifest_sha256=b.sha(MANIFEST),launcher_sha256=b.sha(ENTRY),only_runtime_change='ddraw.ini game_handles_close'))
 print(action,'wrapper close policy passed')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
