"""Character SpriteBar clipping delta, preserving all installed feature modules."""
import argparse,shutil,json,subprocess
import build_11_surface_lifecycle as base
import build_remastered_11 as b
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-character-icons'
BACK=b.ROOT/'modernization/backups/remastered-1.1-character-icons'
def build():
    OUT.mkdir(exist_ok=False)
    for p in base.OUT.iterdir():
        if p.suffix in ('.cpp','.h','.inc','.rc','.cmd','.ico') or p.name=='repath.dll':shutil.copy2(p,OUT/p.name)
    assert resources(b.TARGET/'MagicMayhem-Remastered-1.1.exe')[102]==(base.OUT/'qol_bindings.dll').read_bytes()
    old=(base.OUT/'campaign_ui.cpp').read_text(encoding='utf-8');new=(b.SRC/'campaign_ui.cpp').read_text(encoding='utf-8')
    assert new.replace(new[new.index('void __fastcall spritebar_clip'):new.index('int scale()')],'').replace('        {0x4dd718,0x57dc60,(void*)spritebar_clip},\n','')==old
    (OUT/'campaign_ui.cpp').write_text(new,encoding='utf-8')
    subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
    for name in ['candidate.exe','release.exe']:
        assert resources(OUT/name)[101]==resources(b.TARGET/'MagicMayhem-Remastered-1.1.exe')[101]
    base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
    base.write(OUT/'verification.json',dict(result='passed',module_sha256=b.sha(OUT/'qol_bindings.dll'),scope='SpriteBar clipping on UI only; native battle unchanged',runtime_acceptance='pending isolated save2 comparison'))
def run(action):
    if action=='build':build();return
    if action=='install':
        v=json.loads((OUT/'verification.json').read_text());assert v.get('save2_verified')
    base.OUT=OUT;base.BACK=BACK
    if action=='install':base.install('character_spritebar_fix')
    else:base.rollback()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
