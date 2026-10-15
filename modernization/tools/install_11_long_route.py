"""Hash-gated save17 long-route installation; preserves latest other modules."""
import argparse
import hashlib
import json
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources

base.OUT = base.b.ROOT / 'modernization/build/remastered-1.1-long-route-v2'
base.BACK = base.b.ROOT / 'modernization/backups/remastered-1.1-long-route-v2'

def install():
    verification = json.loads((base.OUT / 'verification.json').read_text())
    assert verification['result'] == 'passed' and verification['checks'] == 37
    assert verification['module_sha256'] == base.b.sha(base.OUT / 'repath.dll')
    assert (base.OUT / 'long_route.inc').read_bytes() == (base.b.SRC / 'long_route.inc').read_bytes()
    for entry, manifest, kind in base.targets():
        m = json.loads(manifest.read_text(encoding='utf-8'))
        assert base.b.sha(entry) == m['launcher_sha256']
        assert base.b.sha(entry.parent / 'runtime/Chaos-Wide169-engine.exe') == m['engine_sha256'] == '42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
        current = resources(entry)
        candidate = resources(base.OUT / ('candidate.exe' if kind == 'candidate' else 'release.exe'))
        assert set(current) == set(candidate)
        assert candidate[101] == (base.OUT / 'repath.dll').read_bytes()
        assert all(candidate[i] == current[i] for i in current if i != 101)
    verification.update(
        runtime_acceptance='pending user testing; user requested installation without further gameplay runs',
        save17_fixture_sha256='03aefae5b9f3f11e133da82fcf64633fac4830da5a9b79a6a1d45fa304d273c2',
        save17_runtime_observation='Candidate took northward long detour; complete arrival not verified. Story/combat interferes with automated observation.',
        search_limits={'nodes': 16384, 'expansions': 8192, 'cached_points': 512, 'engine_segment_points': 16},
    )
    base.write(base.OUT / 'verification.json', verification)
    base.install('save17_long_route')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['install', 'rollback'])
    if p.parse_args().action == 'install':
        install()
    else:
        base.rollback()
