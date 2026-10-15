"""Restore wrongly excluded game MAP sections with hash checks and rollback."""
import json,shutil
from pathlib import Path
import release_remastered_11 as r
from install_11_minimap_v2 import idle,replace
import build_remastered_11 as b

def main():
    idle()
    source=json.loads((r.SOURCE/'manifest.json').read_text(encoding='utf-8'))
    maps={n:h for n,h in source['files'].items() if n.lower().startswith('realms/') and n.lower().endswith('.map')}
    assert len(maps)==683
    roots=[r.STAGE,r.DEST]
    backup=b.ROOT/'modernization/backups/remastered-1.1-release-map-sections'
    backup.mkdir(exist_ok=False)
    changes={};originals={};created=[]
    for idx,root in enumerate(roots):
        manifest=root/'release-manifest.json';m=json.loads(manifest.read_text(encoding='utf-8'))
        assert b.sha(root/r.ENTRY)==m['launcher_sha256']
        originals[manifest]=manifest.read_bytes();(backup/f'manifest-{idx}.json').write_bytes(originals[manifest])
        for name,digest in maps.items():
            src=r.RUNTIME/name;assert r.sha(src)==digest
            dst=root/'runtime'/name;assert not dst.exists(),'Do not overwrite player resources'
            created.append(dst);changes[dst]=src.read_bytes();m['files']['runtime/'+name]=digest
        m['map_sections_repair']=dict(date='2026-10-01',restored=len(maps),cause='game MAP data incorrectly classified as linker build output',validation='all683 native map hashes match development manifest; user new-game test pending')
        changes[manifest]=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    try:
        for path,data in changes.items():path.parent.mkdir(parents=True,exist_ok=True);replace(path,data)
        for root in roots:
            m=json.loads((root/'release-manifest.json').read_text(encoding='utf-8'))
            assert all(r.sha(root/'runtime'/n)==h for n,h in maps.items())
            # Excluded player-state files may be consumed/modified by startup.
            for n,h in m['files'].items():
                if n not in m['mutable_files']:assert r.sha(root/n)==h,n
    except BaseException:
        for path in created:
            assert path.resolve().is_relative_to(r.STAGE.resolve()) or path.resolve().is_relative_to(r.DEST.resolve())
            path.unlink(missing_ok=True)
        for path,raw in originals.items():replace(path,raw)
        raise
    provenance=r.OUT/'provenance.json';raw=provenance.read_bytes();(backup/'provenance.json').write_bytes(raw)
    p=json.loads(raw);p['omitted']=[n for n in p['omitted'] if n not in maps];p['source_files'].update(maps);b.write(provenance,p)
    verify=r.OUT/'verification.json';(backup/'verification.json').write_bytes(verify.read_bytes());v=json.loads(verify.read_text(encoding='utf-8'))
    m=json.loads((r.STAGE/'release-manifest.json').read_text(encoding='utf-8'));v.update(files=len(m['files']),map_sections_restored=len(maps),runtime_acceptance='user new-game testing pending');b.write(verify,v)
    b.write(backup/'installation.json',dict(added=[str(p) for p in created],manifests={str(p):r.sha(p) for p in originals},backup=str(backup),rollback='with game closed restore backed-up manifests and remove only listed hash-verified MAP additions',maps=maps))
    print('Restored683 MAP files in release and frozen package; all static files verified')

if __name__=='__main__':main()
