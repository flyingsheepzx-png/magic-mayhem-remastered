"""v31: opt-in terrain tracing; preserve v30 launcher except pinned DLL hash."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
import pefile
from install_path_review import ROOT,ENTRY,BASE,STATE,ENGINE,sha,write,idle,baseline_identity,resources

BUILD=ROOT/'modernization/build/terrain-trace-v1'
PACKAGE=ROOT/'modernization/build/wide169/package-v31-terrain-trace'
DLL=ROOT/'game-wide169/terrain_diagonal.dll'
OLD='aca872718155d51b39c8c74ab41cb7801dc7fc1ff7807ab05acf8b559839ade1'
OLD_DLL='0a18ddae17025d16b44197b4eddca09685a63c1a8dbac130d9c3e1e5d7068391'

def parent():
    baseline_identity()
    assert sha(ENTRY)==OLD and sha(DLL)==OLD_DLL
    assert sha(ROOT/'game-wide169/Chaos-Wide169-engine.exe')==ENGINE

def build():
    parent();BUILD.mkdir(parents=True,exist_ok=True)
    source=ROOT/'modernization/runtime/terrain_diagonal/terrain_diagonal.cpp'
    shutil.copy2(source,BUILD/source.name)
    (BUILD/'build.cmd').write_text('@echo off\ncall "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\VC\\Auxiliary\\Build\\vcvarsall.bat" x86 >nul\n'
        'if errorlevel 1 exit /b 1\ncl /nologo /LD /O2 /EHsc /W4 terrain_diagonal.cpp /link /OUT:terrain_diagonal.dll /MAP:terrain.map\n')
    subprocess.run(['cmd','/c','build.cmd'],cwd=BUILD,check=True)
    digest=sha(BUILD/DLL.name)
    original=ENTRY.read_bytes();old=OLD_DLL.encode('utf-16le');new=digest.encode('utf-16le')
    assert original.count(old)==1
    offset=original.index(old);p=pefile.PE(data=original)
    section=p.get_section_by_rva(p.get_rva_from_offset(offset))
    assert section.Name.rstrip(b'\0')==b'.rdata'
    candidate=original[:offset]+new+original[offset+len(old):]
    target=BUILD/ENTRY.name;target.write_bytes(candidate)
    assert candidate.replace(new,old,1)==original
    assert resources(target)==resources(ENTRY)
    write(BUILD/'manifest.json',dict(parent_sha256=OLD,parent_dll_sha256=OLD_DLL,
        launcher_sha256=sha(target),terrain_sha256=digest,source_sha256=sha(source),
        launcher_hash_offset=offset,validation='Build/integrity and offline terrain comparison; user gameplay pending'))

def install():
    idle();parent();assert not PACKAGE.exists()
    report=json.loads((BUILD/'manifest.json').read_text())
    assert sha(BUILD/ENTRY.name)==report['launcher_sha256']
    assert sha(BUILD/DLL.name)==report['terrain_sha256']
    state=json.loads(STATE.read_text());previous=Path(state['package'])
    backup=ROOT/'modernization/backups/wide169'/('terrain-trace-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    for p in (ENTRY,DLL,BASE,STATE):shutil.copy2(p,backup/p.name)
    protected={p:sha(p) for folder in ('game-wide169/Save','game-wide169/CFG','modernization/config')
               for p in (ROOT/folder).glob('*') if p.is_file()}
    protected[ROOT/'game-wide169/Chaos-Wide169-engine.exe']=ENGINE
    shutil.copytree(previous/'runtime',PACKAGE/'runtime')
    shutil.copy2(BUILD/ENTRY.name,PACKAGE/ENTRY.name)
    shutil.copy2(BUILD/DLL.name,PACKAGE/'runtime'/DLL.name)
    spec=json.loads((previous/'manifest.json').read_text())
    spec.update(parent_package=str(previous),launcher_sha256=report['launcher_sha256'],
                terrain_trace=report,validation=report['validation'])
    spec['files'][DLL.name]=report['terrain_sha256'];write(PACKAGE/'manifest.json',spec)
    try:
        shutil.copy2(BUILD/DLL.name,DLL);shutil.copy2(BUILD/ENTRY.name,ENTRY)
        baseline=json.loads(BASE.read_text())
        baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe']=sha(ENTRY)
        baseline['latest_development']['files']['game-wide169/terrain_diagonal.dll']=sha(DLL)
        state.update(package=str(PACKAGE),manifest_sha256=sha(PACKAGE/'manifest.json'),terrain_trace_backup=str(backup))
        write(BASE,baseline);write(STATE,state)
        assert sha(ENTRY)==report['launcher_sha256'] and sha(DLL)==report['terrain_sha256']
        assert all(sha(p)==h for p,h in protected.items());baseline_identity()
    except BaseException:
        for p in (ENTRY,DLL,BASE,STATE):shutil.copy2(backup/p.name,p)
        raise
    write(backup/'installed.json',report)
    print(json.dumps(dict(status='installed',backup=str(backup),sha256=sha(ENTRY))))

def rollback():
    idle();baseline_identity();state=json.loads(STATE.read_text());assert state['package']==str(PACKAGE)
    backup=Path(state['terrain_trace_backup']);report=json.loads((backup/'installed.json').read_text())
    assert sha(ENTRY)==report['launcher_sha256'] and sha(DLL)==report['terrain_sha256']
    assert sha(backup/ENTRY.name)==OLD and sha(backup/DLL.name)==OLD_DLL
    for p in (ENTRY,DLL,BASE,STATE):shutil.copy2(backup/p.name,p)
    baseline_identity();print('Restored exact v30 launcher, terrain DLL and manifests.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','install','rollback'])
    globals()[parser.parse_args().action]()
