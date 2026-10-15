"""Preserve Tab input module; add private roof-clipped-unit body rendering."""
import argparse,json,shutil,subprocess
import build_11_roof_tab as tab
from install_11_minimap_v2 import resources
b=tab.b;base=tab.base
OUT=b.ROOT/'modernization/build/remastered-1.1-roof-ghost'
BACK=b.ROOT/'modernization/backups/remastered-1.1-roof-ghost'
SOURCE=b.ROOT/'modernization/build/remastered-1.1-wrap-route-v1'
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(tab.OUT/'release.exe')
 assert current[101]==(SOURCE/'repath.dll').read_bytes()
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.dll'):shutil.copy2(p,OUT/p.name)
 (OUT/'qol_bindings.dll').write_bytes(current[102])
 shutil.copy2(b.SRC/'roof_ghost.inc',OUT/'roof_ghost.inc')
 p=OUT/'render_replay_trial.cpp';s=p.read_text()
 s=b.replace_once(s,'static void draw_occluded_units(unsigned char* buffer,double fraction) {',
 '#include "roof_ghost.inc"\nstatic void draw_occluded_units(unsigned char* buffer,double fraction) {')
 s=b.replace_once(s,'    bool any=false;','    bool any=roof_count>0;')
 s=b.replace_once(s,'    for(int i=0;i<command_count;i++)if(body_commands[i] && owners[i]>=0){\n        const Command& c=saved[i];',
 '''    for(int j=-roof_count;j<command_count;j++){
        bool ghost=j<0;int i=ghost?j+roof_count:j;
        if(!ghost && (!body_commands[i] || owners[i]<0))continue;
        int actor=ghost?roof_owners[i]:owners[i];
        const Command& c=ghost?roof_bodies[i]:saved[i];''')
 s=b.replace_once(s,'projected_shift(actors[owners[i]],fraction,&dx,&dy);\n        int x=',
 'projected_shift(actors[actor],fraction,&dx,&dy);\n        int x=')
 s=b.replace_once(s,'    before_draw(scene,queue,buffer);\n    native_bars_shifted=false;',
 '    before_draw(scene,queue,buffer);\n    roof_collect(scene);\n    native_bars_shifted=false;')
 p.write_text(s)
 base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()
def verify():
 current=resources(tab.OUT/'release.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  assert all(r[i]==((OUT/'repath.dll').read_bytes() if i==101 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name!='render_replay_trial.cpp':assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
def install():
 verify()
 reports=[json.loads((OUT/name).read_text()) for name in ('ghost-verification.json','wrap-verification.json','command-verification.json','verification.json')]
 assert all(v['result']=='passed' and v['module_sha256']==b.sha(OUT/'repath.dll') for v in reports)
 assert [v['checks'] for v in reports]==[52,24,43,37]
 assert (OUT/'roof_ghost.inc').read_bytes()==(b.SRC/'roof_ghost.inc').read_bytes()
 for e,m,k in base.targets():assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 base.write(OUT/'verification.json',dict(result='passed',checks=156,module_sha256=b.sha(OUT/'repath.dll'),reports=reports,runtime_acceptance='pending user latest bridge-save testing'))
 base.OUT=OUT;base.BACK=BACK;base.install('roof_hidden_unit_ghost')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
