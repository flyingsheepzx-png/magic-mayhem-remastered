"""Recreated Portmanteau Sprite ownership fix; retain AI diagnostics verbatim."""
import argparse,hashlib,json,shutil,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-port-preview'
BACK=b.ROOT/'modernization/backups/remastered-1.1-port-preview'
AI=b.ROOT/'modernization/build/remastered-1.1-ai-diagnostics'
CHAR=b.ROOT/'modernization/build/remastered-1.1-character-icons'

def build():
    rows=[]
    for e,m,k in base.targets():
        manifest=json.loads(m.read_text(encoding='utf-8'))
        assert b.sha(e)==manifest['launcher_sha256']
        assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
        for key,name in [(101,'repath.dll'),(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]:
            assert resources(e)[key]==(AI/name).read_bytes()
        rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
    OUT.mkdir(exist_ok=False)
    for p in CHAR.iterdir():
        if p.suffix in ('.cpp','.h','.inc','.ico'):shutil.copy2(p,OUT/p.name)
    for name in ['launcher.cpp','release_launcher.cpp','candidate.rc','release.rc','repath.dll','ai_diagnostics.dll']:
        shutil.copy2(AI/name,OUT/name)
    shutil.copy2(b.SRC/'mixed_ui_fonts.cpp',OUT/'mixed_ui_fonts.cpp')
    cmd=(CHAR/'build.cmd').read_text().replace('/OUT:qol_bindings.dll','/OUT:qol_bindings.dll /MAP:qol_bindings.map')
    (OUT/'build.cmd').write_text(cmd)
    base.write(OUT/'before.json',rows)
    subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
    verify()

def verify():
    for name in ['candidate.exe','release.exe']:
        r=resources(OUT/name)
        for key,file in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]:assert r[key]==(AI/file).read_bytes()
        assert r[102]==(OUT/'qol_bindings.dll').read_bytes()
    subprocess.run([b.PYTHON if hasattr(b,'PYTHON') else 'C:/Python314/python.exe',str(b.ROOT/'modernization/tools/verify_11_port_preview.py')],check=True)

def install():
    verify()
    base.OUT=OUT;base.BACK=BACK;base.install('port_preview_recreation_fix')

def rollback():
    base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify','install','rollback']);globals()[p.parse_args().action]()
