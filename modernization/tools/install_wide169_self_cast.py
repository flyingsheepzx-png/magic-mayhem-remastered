"""Install or roll back the portrait self-cast launcher without touching saves."""
import argparse
import json
import shutil
import time

from wide169_build import ROOT, GAME, BUILD, sha, write_json
from verify_hd60_runtime import configured_kernel, processes

STATE=ROOT/'modernization/wide169-installed.json'
BASELINE=ROOT/'modernization/current-baseline.json'
TARGET=GAME/'Chaos-Wide169-Trial.exe'
PARENT=BUILD/'package-v9-repeat-self-cast'
PACKAGE=BUILD/'package-v10-portrait-heal'
BACKUP_ROOT=ROOT/'modernization/backups/wide169'

def idle():
    if any(name.startswith('chaos') for _,_,name in processes(configured_kernel())):
        raise RuntimeError('Close game processes before changing the launcher')

def install():
    idle()
    baseline=json.loads(BASELINE.read_text())
    prior=json.loads(STATE.read_text())
    expected=baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe']
    if sha(TARGET.read_bytes())!=expected or sha((PARENT/TARGET.name).read_bytes())!=expected:
        raise RuntimeError('Unknown current widescreen launcher')
    if prior['status']!='installed' or prior['package']!=str(PARENT):
        raise RuntimeError('Unexpected installed package')
    if sha((PARENT/'manifest.json').read_bytes())!=prior['manifest_sha256']:
        raise RuntimeError('Parent package manifest mismatch')
    candidate=ROOT/'modernization/build'/TARGET.name
    if not candidate.is_file() or PACKAGE.exists():
        raise RuntimeError('Candidate missing or immutable v10 package already exists')
    backup=BACKUP_ROOT/('portrait-heal-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    shutil.copy2(TARGET,backup/TARGET.name)
    shutil.copytree(PARENT/'runtime',PACKAGE/'runtime')
    shutil.copy2(candidate,PACKAGE/TARGET.name)
    spec=json.loads((PARENT/'manifest.json').read_text())
    spec['parent_package']=str(PARENT)
    spec['launcher_sha256']=sha(candidate.read_bytes())
    write_json(PACKAGE/'manifest.json',spec)
    shutil.copy2(candidate,TARGET)
    if sha(TARGET.read_bytes())!=spec['launcher_sha256']:
        shutil.copy2(backup/TARGET.name,TARGET)
        raise RuntimeError('Launcher copy failed; original restored')
    prior.update(package=str(PACKAGE),manifest_sha256=sha((PACKAGE/'manifest.json').read_bytes()),
                 self_cast_backup=str(backup))
    write_json(STATE,prior)
    baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe']=spec['launcher_sha256']
    baseline['latest_development']['installed_manifest']='modernization/wide169-installed.json'
    write_json(BASELINE,baseline)
    print(json.dumps(dict(status='installed',launcher_sha256=spec['launcher_sha256'],backup=str(backup))))

def rollback():
    idle()
    prior=json.loads(STATE.read_text())
    backup=__import__('pathlib').Path(prior['self_cast_backup'])/TARGET.name
    spec=json.loads((PACKAGE/'manifest.json').read_text())
    old=json.loads((PARENT/'manifest.json').read_text())['launcher_sha256']
    if sha(TARGET.read_bytes())!=spec['launcher_sha256'] or sha(backup.read_bytes())!=old:
        raise RuntimeError('Launcher or backup identity mismatch')
    shutil.copy2(backup,TARGET)
    prior.update(package=str(PARENT),manifest_sha256=sha((PARENT/'manifest.json').read_bytes()))
    prior.pop('self_cast_backup',None)
    write_json(STATE,prior)
    baseline=json.loads(BASELINE.read_text())
    baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe']=old
    write_json(BASELINE,baseline)
    print(json.dumps(dict(status='rolled_back',launcher_sha256=old)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('install','rollback'))
    globals()[parser.parse_args().action]()
