"""Build/install portable mixed composition, preserving current launcher modules."""
import argparse,json,shutil,subprocess
from pathlib import Path
import build_remastered_11 as b
import build_11_surface_lifecycle as lifecycle
import portable_11_wrapper as portable
from build_11_fmv_h264 import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-portable-render'
BACK=b.ROOT/'modernization/backups/remastered-1.1-portable-render'
OLD='d4beb210c7847bdf0a201b8f69a4fa6dc4adf65eb94a69ced52b6905c4827640'
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build():
    OUT.mkdir(exist_ok=False);source=b.BUILD/'wrapper'
    assert b.sha(source/'bin/Release/ddraw.dll')==OLD
    rows=[]
    for entry,manifest,kind in lifecycle.targets():
        p=entry.parent/'runtime/ddraw.dll';m=json.loads(manifest.read_text(encoding='utf-8'))
        assert b.sha(p)==OLD and b.sha(entry)==m['launcher_sha256']
        rows.append(dict(wrapper=str(p),manifest=str(manifest),kind=kind,launcher=str(entry),launcher_sha256=b.sha(entry),manifest_sha256=b.sha(manifest)))
    ws=OUT/'wrapper';shutil.copytree(source,ws,ignore=shutil.ignore_patterns('.git','bin','obj','Debug','Release','.vs'))
    portable.apply(ws)
    subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
    shutil.copy2(b.ROOT/'modernization/tests/portable_engine_identity.cpp',OUT/'identity_test.cpp')
    shutil.copy2(b.ROOT/'modernization/wrapper-probe/mm_engine_identity.h',OUT/'mm_engine_identity.h')
    (OUT/'test.cmd').write_text('''@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc identity_test.cpp /link /OUT:identity_test.exe
''')
    subprocess.run(['cmd','/c','test.cmd'],cwd=OUT,check=True)
    engine=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
    moved=OUT/'任意目录/Chaos-Wide169-engine.exe';moved.parent.mkdir();shutil.copy2(engine,moved)
    unknown=OUT/'unknown.exe';raw=bytearray(engine.read_bytes());raw[-1]^=1;unknown.write_bytes(raw)
    for p,allowed in [(engine,1),(lifecycle.DEST/'runtime/Chaos-Wide169-engine.exe',1),(moved,1),(unknown,0),(OUT/'missing.exe',0)]:
        subprocess.run([str(OUT/'identity_test.exe'),str(p),str(allowed)],check=True)
    write(OUT/'before.json',rows)
    write(OUT/'verification.json',dict(result='passed',engine_gate='known engine accepted in candidate, formal release and moved Unicode directory; modified/missing engine refused',wrapper_sha256=b.sha(ws/'bin/Release/ddraw.dll'),runtime_acceptance='pending isolated save1 comparison'))
def install():
    lifecycle.idle();rows=json.loads((OUT/'before.json').read_text());v=json.loads((OUT/'verification.json').read_text())
    assert v['result']=='passed' and v.get('save1_comparison',{}).get('result')=='passed'
    dll=OUT/'wrapper/bin/Release/ddraw.dll';assert b.sha(dll)==v['wrapper_sha256'];BACK.mkdir(exist_ok=False);changes=[]
    for i,r in enumerate(rows):
        p=Path(r['wrapper']);manifest=Path(r['manifest'])
        assert b.sha(p)==OLD and b.sha(manifest)==r['manifest_sha256'] and b.sha(Path(r['launcher']))==r['launcher_sha256']
        m=json.loads(manifest.read_text(encoding='utf-8'));key='ddraw.dll' if r['kind']=='candidate' else 'runtime/ddraw.dll'
        m['files'][key]=v['wrapper_sha256'];m['portable_mixed_render']=v
        for j,(dest,data) in enumerate([(p,dll.read_bytes()),(manifest,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode())]):
            backup=BACK/f'{i}-{j}.bak';backup.write_bytes(dest.read_bytes());changes.append(dict(path=str(dest),backup=str(backup),before_sha256=b.sha(dest),after_sha256=__import__('hashlib').sha256(data).hexdigest(),data=data))
    write(BACK/'rollback.json',[{k:v for k,v in r.items() if k!='data'} for r in changes])
    try:
        for r in changes:replace(Path(r['path']),r['data']);assert b.sha(Path(r['path']))==r['after_sha256']
    except BaseException:
        for r in changes:replace(Path(r['path']),Path(r['backup']).read_bytes())
        raise
    print('Installed portable mixed rendering; launcher/modules/assets/save unchanged')
def rollback():
    lifecycle.idle();rows=json.loads((BACK/'rollback.json').read_text())
    for r in rows:assert b.sha(Path(r['path']))==r['after_sha256'] and b.sha(Path(r['backup']))==r['before_sha256']
    for r in rows:replace(Path(r['path']),Path(r['backup']).read_bytes());assert b.sha(Path(r['path']))==r['before_sha256']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
