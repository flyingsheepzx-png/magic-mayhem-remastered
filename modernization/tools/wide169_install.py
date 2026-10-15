"""Hash-gated package, rollback and reinstall for the isolated 16:9 runtime."""
from pathlib import Path
import argparse,json,shutil,time
from wide169_build import ROOT,GAME,LAB,BUILD,sha,write_json
from verify_hd60_runtime import configured_kernel,processes

PACKAGE=BUILD/'package-v7-dialog-grimoire-selection'
STATE=ROOT/'modernization/wide169-installed.json'
LAUNCHER=GAME/'Chaos-Wide169-Trial.exe'

def idle():
    if any(n.startswith('chaos') for _,_,n in processes(configured_kernel())):
        raise RuntimeError('Close game instances first')

def files(folder):
    for p in folder.rglob('*'):
        if p.is_file() and not any(x in ('modernization','ss') for x in p.relative_to(folder).parts):yield p
    config=folder/'modernization/config/qol-hotkeys.json'
    if config.is_file():yield config

def inventory(folder):return {p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in files(folder)}

def fallback():
    baseline=json.loads((ROOT/'modernization/current-baseline.json').read_text())
    for name in ('Chaos.exe','Chaos-HD60-engine.exe','Chaos-HD60-Trial.exe'):
        if sha((GAME/name).read_bytes())!=baseline['files'][name]:raise RuntimeError('Fallback identity changed: '+name)
    return {p.relative_to(GAME).as_posix():sha(p.read_bytes()) for p in files(GAME) if p!=LAUNCHER}

def package():
    idle();fallback()
    if PACKAGE.exists():raise RuntimeError('Package already exists; preserve it and choose a new package revision')
    current,previous=manifest()
    engine=json.loads((BUILD/'engine.json').read_text())
    if engine['sha256']!=previous['engine_sha256']:raise RuntimeError('Candidate engine mismatch')
    source=Path(current['package'])
    if source.resolve()!=BUILD/'package-v5-input-map':raise RuntimeError('Unexpected parent package')
    shutil.copytree(source/'runtime',PACKAGE/'runtime')
    candidate=ROOT/'modernization/build/Chaos-Wide169-Trial.exe'
    if not candidate.is_file():raise RuntimeError('Candidate launcher missing')
    shutil.copy2(candidate,PACKAGE/LAUNCHER.name)
    spec=dict(kind='wide169-independent-package',engine_sha256=engine['sha256'],
        files=inventory(PACKAGE/'runtime'),launcher_sha256=sha(LAUNCHER.read_bytes()),
        native_canvas=[1280,720],output=[2560,1440],logic_preference=30)
    spec['launcher_sha256']=sha((PACKAGE/LAUNCHER.name).read_bytes())
    write_json(PACKAGE/'manifest.json',spec)
    return dict(status='packaged',files=len(spec['files']),manifest_sha256=sha((PACKAGE/'manifest.json').read_bytes()))

def manifest():
    state=json.loads(STATE.read_text());source=Path(state['package']);raw=(source/'manifest.json').read_bytes()
    if sha(raw)!=state['manifest_sha256']:raise RuntimeError('Package manifest changed')
    m=json.loads(raw)
    if inventory(source/'runtime')!=m['files'] or sha((source/LAUNCHER.name).read_bytes())!=m['launcher_sha256']:
        raise RuntimeError('Package content changed')
    return state,m

def check():
    state,m=manifest();fallback()
    if not LAB.is_dir() or not LAUNCHER.is_file():raise RuntimeError('Independent installation absent')
    actual=inventory(LAB);mutable=lambda n:n.startswith(('Save/','CFG/Encrypted/')) or n in ('AI/EXPERIEN.DAT','AI/Brain.dat','CFG/prefs.cfg','ddraw.ini','modernization/config/qol-hotkeys.json')
    changed=[n for n,h in m['files'].items() if not mutable(n) and actual.get(n)!=h]
    extra=[n for n in actual if n not in m['files'] and not mutable(n)]
    if changed or extra or sha(LAUNCHER.read_bytes())!=m['launcher_sha256']:raise RuntimeError('Installation mismatch: '+str(changed+extra))
    return dict(status='verified',files=len(actual),engine_sha256=m['engine_sha256'])

def rollback():
    idle();check();before=fallback();state,m=manifest()
    parked=ROOT/'modernization/backups/wide169'/('rollback-'+str(time.time_ns()))
    parked.mkdir(parents=True)
    # Move the complete runtime, including independent saves. No recursive delete.
    if LAB.resolve()!=ROOT.resolve()/'game-wide169' or parked.resolve().parent!=ROOT.resolve()/'modernization/backups/wide169':
        raise RuntimeError('Rollback paths outside intended workspace')
    LAB.rename(parked/'runtime');LAUNCHER.rename(parked/LAUNCHER.name)
    if fallback()!=before:raise RuntimeError('Fallback files changed during rollback')
    state.update(status='rolled-back',parked=str(parked));write_json(STATE,state)
    return dict(status='rolled-back',preserved_runtime=str(parked),fallback_unchanged=True)

def install():
    idle();before=fallback();state=json.loads(STATE.read_text())
    raw=(PACKAGE/'manifest.json').read_bytes();m=json.loads(raw)
    if inventory(PACKAGE/'runtime')!=m['files'] or sha((PACKAGE/LAUNCHER.name).read_bytes())!=m['launcher_sha256']:raise RuntimeError('Candidate package changed')
    if LAB.exists() or LAUNCHER.exists():raise RuntimeError('Installation destination already exists; verify or rollback it first')
    shutil.copytree(PACKAGE/'runtime',LAB)
    if state.get('parked'):
        old=Path(state['parked'])/'runtime'
        for p in files(old):
            rel=p.relative_to(old)
            if rel.parts[0]=='Save' or rel.parts[:2]==('CFG','Encrypted') or rel.as_posix() in ('AI/EXPERIEN.DAT','AI/Brain.dat','CFG/prefs.cfg','ddraw.ini','modernization/config/qol-hotkeys.json'):
                (LAB/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,LAB/rel)
    (LAB/'modernization/logs').mkdir(parents=True);(LAB/'ss').mkdir()
    shutil.copy2(PACKAGE/LAUNCHER.name,LAUNCHER)
    if fallback()!=before:raise RuntimeError('Fallback files changed during install')
    state.update(status='installed',package=str(PACKAGE),manifest_sha256=sha(raw));write_json(STATE,state)
    return dict(**check(),fallback_unchanged=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['package','check','rollback','install']);a=p.parse_args()
    print(json.dumps(globals()[a.action](),indent=2))
