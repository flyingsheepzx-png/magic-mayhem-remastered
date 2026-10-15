"""Install one guarded allowance change on exact latest installed 1.1 modules."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources

OUT=b.ROOT/'modernization/build/remastered-1.1-ai-budget300'
BACK=b.ROOT/'modernization/backups/remastered-1.1-ai-budget300'
SOURCE=b.ROOT/'modernization/build/remastered-1.1-portrait-ready'
ENGINE='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'

def build():
    current=resources(base.DEST/base.ENTRY)
    assert current==resources(SOURCE/'candidate.exe'), 'Unknown current module set'
    rows=[]
    for e,m,k in base.targets():
        manifest=json.loads(m.read_text(encoding='utf-8'))
        assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
        assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']==ENGINE
        rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
    OUT.mkdir(exist_ok=False)
    for p in SOURCE.iterdir():
        if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.bin'):
            shutil.copy2(p,OUT/p.name)
    for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]:
        (OUT/name).write_bytes(current[i])
    shutil.copy2(b.SRC/'ai_budget.cpp',OUT/'ai_budget.cpp')
    p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
    s=b.replace_once(s,'extern "C" bool mm_install_surface_lifecycle();',
                     'extern "C" bool mm_install_surface_lifecycle();\nextern "C" bool mm_install_ai_budget();')
    s=b.replace_once(s,'return mm_install_surface_lifecycle() &&',
                     'return mm_install_ai_budget() && mm_install_surface_lifecycle() &&')
    p.write_text(s,encoding='utf-8')
    p=OUT/'build.cmd';s=p.read_text()
    s=b.replace_once(s,'portrait_sprite_ready.cpp /link','portrait_sprite_ready.cpp ai_budget.cpp /link')
    p.write_text(s)
    base.write(OUT/'before.json',rows)
    subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
    verify()

def verify():
    current=resources(SOURCE/'candidate.exe')
    for name in ['candidate.exe','release.exe']:
        r=resources(OUT/name)
        assert set(r)==set(current)
        for i in current:
            assert r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i])
    # Existing source files must be retained byte-for-byte except installer chain.
    for p in SOURCE.iterdir():
        if p.suffix in ('.cpp','.h','.inc') and p.name!='qol_bindings.cpp':
            assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
    subprocess.run([sys.executable,str(b.ROOT/'modernization/tests/ai_budget300_test.py')],check=True)

def install():
    verify()
    base.OUT=OUT;base.BACK=BACK;base.install('singleplayer_ai_budget300')
    for e,m,k in base.targets():
        assert resources(e)[102]==(OUT/'qol_bindings.dll').read_bytes()
        assert b.sha(e)==json.loads(m.read_text(encoding='utf-8'))['launcher_sha256']

def rollback():
    base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify','install','rollback'])
    globals()[p.parse_args().action]()
