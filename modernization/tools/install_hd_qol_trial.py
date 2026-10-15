"""Hash-gated install/verify/rollback for the opt-in HD Portmanteau trial."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parents[2]
MANIFEST = PROJECT / 'modernization/hd-qol-trial-installed.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'verify', 'rollback'])
    args = parser.parse_args()
    from hd_qol_background_session import no_game_running
    no_game_running()
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    entry = PROJECT / data['entry']
    source = PROJECT / 'modernization/build/Chaos-HD60-QoL-Trial.exe'
    expected = data['files'][data['entry']]
    baseline = json.loads((PROJECT / 'modernization/current-baseline.json').read_text())
    for name, known in baseline['files'].items():
        if digest(PROJECT / 'game' / name) != known:
            raise RuntimeError(f'Accepted HD baseline changed: {name}')
    for name, known in data['files'].items():
        if name != data['entry'] and digest(PROJECT / name) != known:
            raise RuntimeError(f'Unknown paired file: {name}')
    if args.action == 'install':
        if digest(source) != expected:
            raise RuntimeError('Unknown built trial')
        if entry.exists() and digest(entry) != expected:
            raise RuntimeError('Existing entry is unknown; refusing replacement')
        shutil.copy2(source, entry)
    elif args.action == 'rollback':
        if entry.exists():
            if digest(entry) != expected:
                raise RuntimeError('Unknown installed trial; refusing rollback')
            destination = PROJECT / 'modernization/backups/hd-qol-trial' / expected / entry.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if digest(destination) != expected:
                    raise RuntimeError('Rollback backup changed')
                entry.unlink()
            else:
                shutil.move(entry, destination)
    elif not entry.exists() or digest(entry) != expected:
        raise RuntimeError('Trial entry missing or changed')
    print(json.dumps({'action': args.action, 'installed': entry.exists(),
                      'accepted_hd_preserved': True, 'layout_preserved': True}))


if __name__ == '__main__':
    main()
