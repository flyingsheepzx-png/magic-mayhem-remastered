"""Install or roll back the hash-gated multiunit pathfinding launcher."""
import argparse
import json
import shutil
import time

from wide169_build import ROOT, GAME, BUILD, sha, write_json
from verify_hd60_runtime import configured_kernel, processes

STATE = ROOT/'modernization/wide169-installed.json'
BASELINE = ROOT/'modernization/current-baseline.json'
TARGET = GAME/'Chaos-Wide169-Trial.exe'
PARENT = BUILD/'package-v10-portrait-heal'
PACKAGE = BUILD/'package-v11-multiunit-repath'
CANDIDATE = GAME/'Chaos-Wide169-Multiunit-Diag.exe'


def idle():
    if any(name.startswith('chaos') for _, _, name in processes(configured_kernel())):
        raise RuntimeError('Close game processes before changing the launcher')


def gate():
    baseline = json.loads(BASELINE.read_text())
    state = json.loads(STATE.read_text())
    expected = baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe']
    if expected != '5aadf9f8f1c0ea1e2d6da26d4b32e3ef71d0532280e664b8711d6b35e5484a4f':
        raise RuntimeError('Unknown development baseline')
    if sha(TARGET.read_bytes()) != expected or sha((PARENT/TARGET.name).read_bytes()) != expected:
        raise RuntimeError('Installed launcher differs from v10 parent')
    if state['package'] != str(PARENT) or sha((PARENT/'manifest.json').read_bytes()) != state['manifest_sha256']:
        raise RuntimeError('Installed package identity mismatch')
    return baseline, state


def install():
    idle()
    baseline, state = gate()
    if PACKAGE.exists() or not CANDIDATE.is_file():
        raise RuntimeError('Candidate missing or immutable package exists')
    candidate = CANDIDATE.read_bytes()
    expected_candidate = '01119a189bfd50d3fed7a07d436be66dd02d93266dd259206084b34102c35bc0'
    if sha(candidate) != expected_candidate:
        raise RuntimeError('Candidate hash differs from tested build')
    backup = ROOT/'modernization/backups/wide169'/('multiunit-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    shutil.copy2(TARGET, backup/TARGET.name)
    shutil.copytree(PARENT/'runtime', PACKAGE/'runtime')
    (PACKAGE/TARGET.name).write_bytes(candidate)
    spec = json.loads((PARENT/'manifest.json').read_text())
    spec['parent_package'] = str(PARENT)
    spec['launcher_sha256'] = expected_candidate
    write_json(PACKAGE/'manifest.json', spec)
    try:
        TARGET.write_bytes(candidate)
        if sha(TARGET.read_bytes()) != expected_candidate:
            raise RuntimeError('Launcher copy failed')
        state.update(package=str(PACKAGE), manifest_sha256=sha((PACKAGE/'manifest.json').read_bytes()),
                     multiunit_backup=str(backup))
        baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe'] = expected_candidate
        write_json(STATE, state)
        write_json(BASELINE, baseline)
    except BaseException:
        shutil.copy2(backup/TARGET.name, TARGET)
        raise
    print(json.dumps(dict(status='installed', launcher_sha256=expected_candidate, backup=str(backup))))


def rollback():
    idle()
    state = json.loads(STATE.read_text())
    if state.get('package') != str(PACKAGE):
        raise RuntimeError('v11 is not installed')
    backup = __import__('pathlib').Path(state['multiunit_backup'])/TARGET.name
    old = json.loads((PARENT/'manifest.json').read_text())['launcher_sha256']
    new = json.loads((PACKAGE/'manifest.json').read_text())['launcher_sha256']
    if sha(TARGET.read_bytes()) != new or sha(backup.read_bytes()) != old:
        raise RuntimeError('Launcher or backup identity mismatch')
    shutil.copy2(backup, TARGET)
    state.update(package=str(PARENT), manifest_sha256=sha((PARENT/'manifest.json').read_bytes()))
    state.pop('multiunit_backup', None)
    baseline = json.loads(BASELINE.read_text())
    baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe'] = old
    write_json(STATE, state)
    write_json(BASELINE, baseline)
    print(json.dumps(dict(status='rolled_back', launcher_sha256=old)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('install', 'rollback'))
    globals()[parser.parse_args().action]()
