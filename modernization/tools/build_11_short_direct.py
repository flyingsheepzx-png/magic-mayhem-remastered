"""One isolated path iteration; preserve exact installed UI resource."""
import argparse,json,shutil,subprocess
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources,replace
OUT=b.ROOT/'modernization/build/remastered-1.1-short-direct'
BACK=b.ROOT/'modernization/backups/remastered-1.1-short-direct'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'
def run(action):
 if action=='rollback':
  idle();v=json.loads((BACK/'installation.json').read_text());assert b.sha(ENTRY)==v['launcher_sha256'] and b.sha(MANIFEST)==v['manifest_sha256']
  for p in [ENTRY,MANIFEST]:replace(p,(BACK/p.name).read_bytes())
  b.verify();return
 b.verify()
 if action=='build':
  source=b.BUILD;latest=b.ROOT/'modernization/build/remastered-1.1-minimap-center'
  assert resources(ENTRY)[101]==(source/'repath.dll').read_bytes()
  assert resources(ENTRY)[102]==(latest/'qol_bindings.dll').read_bytes()
  OUT.mkdir(exist_ok=False)
  for n in ['repath_multiunit_trial.cpp','render_replay_trial.cpp','clock_trial.cpp','logic_time_trial.cpp','game_time_trial.cpp','command_index.h','ui_layout.h','layout_context.h']:shutil.copy2(source/n,OUT/n)
  for n in ['launcher.cpp','combined.rc','qol_bindings.dll']:shutil.copy2(latest/n,OUT/n)
  shutil.copy2(b.SRC/'short_direct_route.inc',OUT/'short_direct_route.inc')
  p=OUT/'repath_multiunit_trial.cpp';s=p.read_text();marker='static bool ordinary_wait(void* u) {';assert s.count(marker)==1;s=s.replace(marker,'#include "short_direct_route.inc"\n'+marker)
  marker='        if (!patch(0x512460,(void*)finish_hook,c,7)) return FALSE;';assert s.count(marker)==1
  s=s.replace(marker,'        const unsigned char direct_bytes[]={0x8b,0x8c,0x24,0xc4,0x02,0,0};\n        if (!patch(0x51292f,(void*)short_direct_hook,direct_bytes,7)) return FALSE;\n'+marker);p.write_text(s)
  cmd=(source/'build.cmd').read_text();start=cmd.index('cl /nologo /LD /O2 /EHsc /std:c++17 /W4 qol_bindings.cpp');end=cmd.index('rc /nologo',start);cmd=cmd[:start]+cmd[end:];(OUT/'build.cmd').write_text(cmd)
  subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
  assert resources(OUT/ENTRY.name)[102]==resources(ENTRY)[102]
  b.write(OUT/'build-state.json',dict(launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST)))
 else:
  idle();v=json.loads((OUT/'build-state.json').read_text());t=json.loads((OUT/'verification.json').read_text())
  assert t['result']=='passed' and t['module_sha256']==b.sha(OUT/'repath.dll')
  assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
  BACK.mkdir(exist_ok=False);before={p:p.read_bytes() for p in [ENTRY,MANIFEST]}
  for p,raw in before.items():(BACK/p.name).write_bytes(raw)
  m=json.loads(before[MANIFEST]);m['launcher_sha256']=b.sha(OUT/ENTRY.name);m['short_direct_route']=dict(verification=t,backup=str(BACK),acceptance='test18 user gameplay pending')
  try:
   replace(ENTRY,(OUT/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode());b.verify()
  except BaseException:
   for p,raw in before.items():replace(p,raw)
   raise
  b.write(BACK/'installation.json',dict(launcher_sha256=b.sha(ENTRY),manifest_sha256=b.sha(MANIFEST)))
 print(action,'short direct route passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
