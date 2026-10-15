"""Install the user-approved test10 candidate or restore its exact predecessor."""
import argparse,json,hashlib,shutil,time
from pathlib import Path
from compare_hd_baseline import ROOT,baseline_identity,sha
from verify_hd60_runtime import configured_kernel,processes

BASE=ROOT/'modernization/current-baseline.json'
STATE=ROOT/'modernization/wide169-installed.json'
ENTRY=ROOT/'game/Chaos-Wide169-Trial.exe'
DLL=ROOT/'game-wide169/terrain_diagonal.dll'
PACKAGE=ROOT/'modernization/build/wide169/package-v23-terrain-diagonal'
CANDIDATE=ROOT/'modernization/playtests/terrain-diagonal-v1'
ENTRY_SHA='8ef2806f8c383323f81cb2fb69fde2fdd30ebd208a32bdecbe363418caffa5c3'
DLL_SHA='0a18ddae17025d16b44197b4eddca09685a63c1a8dbac130d9c3e1e5d7068391'

def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def idle():
    if any(n.startswith('chaos') for _,_,n in processes(configured_kernel())):raise RuntimeError('Game running')
def install():
    idle();latest=baseline_identity()
    assert latest['files'][latest['entry']]=='f9c90c345fe295802794b75822b53440d5b84abe11d491115e7e4a2d511f2eaf'
    assert sha(CANDIDATE/'game/Chaos-Terrain-Preview.exe')==ENTRY_SHA
    assert sha(CANDIDATE/'game-wide169/terrain_diagonal.dll')==DLL_SHA
    assert not DLL.exists() and not PACKAGE.exists()
    state=json.loads(STATE.read_text());parent=Path(state['package']);spec=json.loads((parent/'manifest.json').read_text())
    backup=ROOT/'modernization/backups/wide169'/('terrain-diagonal-'+str(time.time_ns()));backup.mkdir(parents=True)
    for p in (ENTRY,BASE,STATE):shutil.copy2(p,backup/p.name)
    protected={p:sha(p) for p in [* (ROOT/'game-wide169/Save').glob('*.sav'),ROOT/'game-wide169/CFG/prefs.cfg']}
    shutil.copytree(parent/'runtime',PACKAGE/'runtime')
    shutil.copy2(CANDIDATE/'game/Chaos-Terrain-Preview.exe',PACKAGE/ENTRY.name)
    shutil.copy2(CANDIDATE/'game-wide169/terrain_diagonal.dll',PACKAGE/'runtime/terrain_diagonal.dll')
    spec.update(parent_package=str(parent),launcher_sha256=ENTRY_SHA,user_authorized_install=True,
                validation='Stationary test10 paired route passed; wider gameplay acceptance delegated to user',automatic_saved_route_refresh=False)
    spec['files']['terrain_diagonal.dll']=DLL_SHA;write(PACKAGE/'manifest.json',spec)
    try:
        shutil.copy2(PACKAGE/'runtime/terrain_diagonal.dll',DLL)
        shutil.copy2(PACKAGE/ENTRY.name,ENTRY)
        assert sha(ENTRY)==ENTRY_SHA and sha(DLL)==DLL_SHA
        state.update(package=str(PACKAGE),manifest_sha256=sha(PACKAGE/'manifest.json'),terrain_diagonal_backup=str(backup))
        baseline=json.loads(BASE.read_text());baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe']=ENTRY_SHA
        baseline['latest_development']['files']['game-wide169/terrain_diagonal.dll']=DLL_SHA
        write(STATE,state);write(BASE,baseline)
        assert all(sha(p)==h for p,h in protected.items())
    except BaseException:
        for p in (ENTRY,BASE,STATE):shutil.copy2(backup/p.name,p)
        # The extra module is inert under the predecessor launcher; preserve it.
        raise
    write(backup/'installed.json',dict(entry_sha256=ENTRY_SHA,dll_sha256=DLL_SHA,protected_unchanged=True))
    print(json.dumps(dict(status='installed',backup=str(backup),entry=str(ENTRY))))
def rollback():
    idle();state=json.loads(STATE.read_text());assert state['package']==str(PACKAGE)
    backup=Path(state['terrain_diagonal_backup']);assert sha(ENTRY)==ENTRY_SHA and sha(DLL)==DLL_SHA
    assert sha(backup/ENTRY.name)=='f9c90c345fe295802794b75822b53440d5b84abe11d491115e7e4a2d511f2eaf'
    for p in (ENTRY,BASE,STATE):shutil.copy2(backup/p.name,p)
    print('Restored v22; unused terrain_diagonal.dll retained for recovery.')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['install','rollback']);globals()[ap.parse_args().action]()
