"""Build/install four portal-only derivatives; executable and maps stay pinned."""
import argparse, json
from PIL import Image
import numpy as np
import build_remastered_11 as b
from install_11_minimap_v2 import idle, replace
from realm_portal_art import PORTALS, composite_portal

OUT = b.ROOT/'modernization/build/remastered-1.1-portal-highlight'
BACK = b.ROOT/'modernization/backups/remastered-1.1-portal-highlight'
RT = b.TARGET/'runtime'
MANIFEST = b.TARGET/'manifest.json'
ENTRY = b.TARGET/'MagicMayhem-Remastered-1.1.exe'

def run(action):
    idle(); b.verify()
    if action == 'rollback':
        state = json.loads((BACK/'installation.json').read_text(encoding='utf-8'))
        assert b.sha(MANIFEST) == state['manifest_sha256']
        assert b.sha(ENTRY) == state['launcher_sha256']
        for row in state['records']:
            assert b.sha(RT/row['path']) == row['sha256']
        for row in state['records']:
            replace(RT/row['path'], (BACK/row['path']).read_bytes())
        replace(MANIFEST, (BACK/'manifest.json').read_bytes()); b.verify(); return
    if action == 'build':
        assert not (OUT/'verification.json').exists(), 'Keep verified build immutable'
        OUT.mkdir(exist_ok=True); records=[]
        for world, region in sorted(PORTALS):
            rel=f'Interface/RealmViewer/hd-selected/{world}_{region:02d}.PNG'
            map_path=RT/f'Interface/RealmViewer/800x600/{world}_Map.PNG'
            matches=[p for p in (RT/'Interface/RealmViewer/800x600').glob('*.pcx')
                     if p.name.lower()==f'{world}_border_{region:02d}.pcx'.lower()]
            assert len(matches)==1; source=matches[0]
            original=b.ROOT/'modernization/releases/remastered-1.0/runtime/runtime'/source.relative_to(RT)
            assert b.sha(source)==b.sha(original), 'Require immutable original portal art'
            approved=b.ROOT/f'modernization/assets/hd/seedvr2-ui-1.1/approved-qwen-maps/{world}_Map.PNG'
            assert b.sha(map_path)==b.sha(approved)
            base=Image.open(map_path).convert('RGB')
            result, alpha=composite_portal(base,Image.open(source))
            pixels=np.array(result); coverage=np.array(alpha); old=np.array(base)
            assert np.array_equal(pixels[coverage==0],old[coverage==0])
            # Vortex interior must retain real authored pixels, rather than tint.
            assert np.count_nonzero(np.any(pixels!=old,axis=2))>1000
            output=OUT/rel;output.parent.mkdir(parents=True,exist_ok=True);result.save(output)
            assert np.array_equal(np.array(Image.open(output)),pixels)
            records.append(dict(path=rel,sha256=b.sha(output),before_sha256=b.sha(RT/rel),
                source=source.relative_to(RT).as_posix(),source_sha256=b.sha(source),
                map=map_path.relative_to(RT).as_posix(),map_sha256=b.sha(map_path),
                outside_exact=True,alpha_bbox=alpha.getbbox()))
        b.write(OUT/'verification.json',dict(result='passed',records=records,
            manifest_before_sha256=b.sha(MANIFEST),launcher_sha256=b.sha(ENTRY),
            art='original keyed portal over approved Qwen map; premultiplied Lanczos edge'))
    else:
        v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
        assert v['result']=='passed' and b.sha(MANIFEST)==v['manifest_before_sha256']
        assert b.sha(ENTRY)==v['launcher_sha256']
        for row in v['records']:
            for path,digest in [(RT/row['path'],row['before_sha256']), (OUT/row['path'],row['sha256']),
                                (RT/row['source'],row['source_sha256']), (RT/row['map'],row['map_sha256'])]:
                assert b.sha(path)==digest
        BACK.mkdir(exist_ok=False);before={MANIFEST:MANIFEST.read_bytes()}
        (BACK/'manifest.json').write_bytes(before[MANIFEST])
        for row in v['records']:
            p=RT/row['path'];before[p]=p.read_bytes();save=BACK/row['path']
            save.parent.mkdir(parents=True,exist_ok=True);save.write_bytes(before[p])
        m=json.loads(before[MANIFEST]);m['portal_highlight_fix']=v
        m['portal_highlight_fix']['backup']=str(BACK)
        m['portal_highlight_fix']['acceptance']='asset checks passed; user test19 acceptance pending'
        for row in v['records']:m['files'][row['path']]=row['sha256']
        try:
            for row in v['records']:replace(RT/row['path'],(OUT/row['path']).read_bytes())
            replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
            assert b.sha(ENTRY)==v['launcher_sha256'];b.verify()
        except BaseException:
            for p,raw in before.items():replace(p,raw)
            raise
        b.write(BACK/'installation.json',dict(records=v['records'],manifest_sha256=b.sha(MANIFEST),launcher_sha256=b.sha(ENTRY)))
    print(action,'portal highlights passed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
