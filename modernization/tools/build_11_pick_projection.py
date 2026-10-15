"""Native picker-space ground projection; preserve latest timing101 and AI102."""
import argparse,json,shutil,subprocess
import build_11_roof_click_floor as prev
import build_11_movement_timing as latest
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-pick-projection'
BACK=b.ROOT/'modernization/backups/remastered-1.1-pick-projection'
SOURCE=prev.OUT;LATEST=latest.OUT

def build():
 current=resources(base.DEST/base.ENTRY)
 assert current==resources(LATEST/'release.exe')
 assert current[102]==(SOURCE/'qol_bindings.dll').read_bytes()
 rows=[]
 for e,m,k in base.targets():
  j=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==j['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==j['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll'):shutil.copy2(p,OUT/p.name)
 for i,n in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/n).write_bytes(current[i])
 for n in ['launcher.cpp','release_launcher.cpp']:shutil.copy2(LATEST/n,OUT/n)
 p=OUT/'canopy_pick.inc';s=p.read_text()
 start=s.index('    // A roof/wall can completely replace');end=s.index('    pick_surface_count=0;',start)
 s=s[:start]+'''    // Reachability does not identify a screen pixel. Never prefer a lower
    // same-column floor unless its projected top surface contains the click.
'''+s[end:]
 start=s.index('        int py=2*(');end=s.index('        int bx=',start)
 s=s[:start]+'''        // Native4f83f0 traverses its current picker/map axes with X(+32,+16)
        // and Y(-32,+16), including after view rotation. Applying camera
        // rotation again here mixes picker space with unrotated world space.
        // Full support height16 means standing/top plane is z+1, not z-1.
        int py=2*(pick_mouse_y-pick_anchor_y+16*(z+1-raw.z));
        int dx=py+px,dy=py-px;
'''+s[end:]
 s=b.replace_once(s,'// The 64x32 native grid diamond is L1 radius64 in fixed coordinates.\n            if(abs(dx-ix*64)+abs(dy-iy*64)>=64)continue;',
 '''// A screen diamond becomes a square in inverse grid coordinates.
            // Half-open ownership prevents overlap and ambiguous edge choices.
            int ux=dx-ix*64,uy=dy-iy*64;
            if(ux<-32 || ux>=32 || uy<-32 || uy>=32)continue;''')
 p.write_text(s)
 base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()

def verify():
 current=resources(LATEST/'release.exe')
 for n in ['candidate.exe','release.exe']:
  r=resources(OUT/n);assert set(r)==set(current)
  assert all(r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name not in ('canopy_pick.inc','launcher.cpp','release_launcher.cpp'):assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
 for n in ['launcher.cpp','release_launcher.cpp']:assert (OUT/n).read_bytes()==(LATEST/n).read_bytes()

def install():
 verify();v=json.loads((OUT/'verification.json').read_text())
 assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 assert (OUT/'canopy_pick.inc').read_bytes()==(b.SRC/'canopy_pick.inc').read_bytes()
 from pathlib import Path
 protected={}
 for e,m,k in base.targets():
  rt=e.parent/'runtime'
  for folder in ['Save','CFG','AI']:
   for p in (rt/folder).rglob('*'):
    if p.is_file():protected[str(p)]=b.sha(p)
  for p in rt.iterdir():
   if p.is_file():protected[str(p)]=b.sha(p)
 base.OUT=OUT;base.BACK=BACK;base.install('pick_projection_correction')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
 for path,digest in protected.items():assert b.sha(Path(path))==digest,path
 base.write(OUT/'installed-verification.json',dict(result='passed',protected_files=len(protected),runtime_settings_saves_ai_unchanged=True))

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
