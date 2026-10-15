"""Restore Portmanteau key binding at native HD UI coordinates."""
import argparse,json,shutil,subprocess
import build_11_canopy_pick as prev
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-port-bindings-hd'
BACK=b.ROOT/'modernization/backups/remastered-1.1-port-bindings-hd'
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
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
 old="""    if(width<800 || width>1280 || height<600 || height>840 ||
       native.x<0 || native.y<0 || native.x>=width || native.y>=height)return false;"""
 new="""    // Mouse and packed slot rectangles already share native UI coordinates.
    // Validate against the current content viewport, not the old 1280x840 cap.
    if(width<=0 || width>8192 || height<=0 || height>8192)return false;
    MmUiViewport viewport=mm_ui_fit(width,height);
    if(native.x<viewport.x || native.y<viewport.y ||
       native.x>=viewport.x+viewport.width || native.y>=viewport.y+viewport.height)return false;"""
 s=b.replace_once(s,old,new)
 p.write_text(s,encoding='utf-8');base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()

def verify():
 current=resources(LATEST/'release.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  assert all(r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name!='qol_bindings.cpp':assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name

def install():
 verify();v=json.loads((OUT/'verification.json').read_text())
 assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('portmanteau_hd_hotkey_binding')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))

def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
