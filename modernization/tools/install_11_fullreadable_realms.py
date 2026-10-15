"""Asset-only, hash-gated install/rollback; never replace executable modules."""
import argparse,json,hashlib,os,shutil
from pathlib import Path
from qwen_fullreadable_realms_11 import OUT,ROOT,sha,save
from build_11_surface_lifecycle import targets,idle
BACK=ROOT/'modernization/backups/remastered-1.1-fullreadable-realms-20261002'
def replace(p,data):
    tmp=p.with_name(p.name+'.fullreadable-new');assert not tmp.exists()
    tmp.write_bytes(data);os.replace(tmp,p)
def install():
    idle();assert not BACK.exists(),'Already installed or unfinished transaction'
    updates={};protected={};checks={}
    for entry,manifest,kind in targets():
        m=json.loads(manifest.read_text(encoding='utf-8'))
        assert sha(entry)==m['launcher_sha256'];protected[str(entry)]=sha(entry)
        engine=entry.parent/'runtime/Chaos-Wide169-engine.exe';assert sha(engine)==m['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da';protected[str(engine)]=sha(engine)
        celtic=entry.parent/'runtime/Interface/RealmViewer/800x600/Celtic_Map.PNG';protected[str(celtic)]=sha(celtic)
        worlds={}
        for world in ['Medieval','Greek']:
            dest=OUT/world;v=json.loads((dest/'verification.json').read_text(encoding='utf-8'))
            for row in v['records']:
                src=dest/'runtime'/row['path'];p=entry.parent/'runtime'/row['path'];assert sha(src)==row['sha256']
                assert sha(p)==row['before_sha256'],'Asset changed since generation: '+str(p)
                if row.get('mask_sha256'):
                    region=int(Path(row['path']).stem.split('_')[-1])
                    masks=[x for x in (entry.parent/'runtime/Interface/RealmViewer/800x600').glob(world+'_*') if '_border_' in x.name.lower() and x.suffix.lower()=='.pcx' and int(x.stem.split('_')[-1])==region]
                    assert len(masks)==1 and sha(masks[0])==row['mask_sha256'],'Mask changed'
                key=('runtime/' if kind=='release' else '')+row['path'];assert m['files'][key]==sha(p),'Manifest mismatch: '+key
                checks[str(p)]=sha(p);updates[p]=src.read_bytes();m['files'][key]=row['sha256']
            worlds[world]={'model':'Qwen Image 2.1','job_id':json.loads((dest/'job.json').read_text(encoding='utf-8'))['manager_job_id'],'target_sha256':v['target_sha256'],'states':v['selected_states'],'runtime_acceptance':'pending user testing'}
        m['fullreadable_realms_20261002']=worlds;checks[str(manifest)]=sha(manifest)
        updates[manifest]=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
    # Keep production source copies aligned; preserve old copies in rollback.
    for world in ['Medieval','Greek']:
        rel=f'Interface/RealmViewer/800x600/{world}_Map.PNG';data=(OUT/world/'runtime'/rel).read_bytes()
        p=ROOT/f'modernization/assets/hd/seedvr2-ui-1.1/approved-qwen-maps/{world}_Map.PNG'
        assert sha(p)==json.loads((OUT/world/'job.json').read_text(encoding='utf-8'))['installed_before_sha256']
        checks[str(p)]=sha(p);updates[p]=data
    BACK.mkdir(parents=True)
    rows=[]
    for index,(p,data) in enumerate(updates.items()):
        original=p.read_bytes();backup=BACK/f'{index:03d}.bin';backup.write_bytes(original)
        rows.append({'path':str(p),'backup':backup.name,'before_sha256':hashlib.sha256(original).hexdigest(),'after_sha256':hashlib.sha256(data).hexdigest()})
    state={'files':rows,'protected':protected,'state':'prepared'};save(BACK/'installation.json',state)
    for p,h in {**checks,**protected}.items():assert sha(Path(p))==h,'Concurrent modification: '+p
    try:
        for p,data in updates.items():replace(p,data)
        for r in rows:assert sha(Path(r['path']))==r['after_sha256']
        for p,h in protected.items():assert sha(Path(p))==h
    except BaseException:
        for r in rows:replace(Path(r['path']),(BACK/r['backup']).read_bytes())
        state['state']='rolled-back-on-error';save(BACK/'installation.json',state);raise
    state['state']='installed';save(BACK/'installation.json',state)
    print('Installed',len(rows),'asset/manifest files; launcher and engine hashes unchanged')
def rollback():
    idle();state=json.loads((BACK/'installation.json').read_text(encoding='utf-8'));assert state['state']=='installed'
    for p,h in state['protected'].items():assert sha(Path(p))==h,'Newer runtime: refuse rollback'
    for r in state['files']:
        assert sha(Path(r['path']))==r['after_sha256'],'Newer file: refuse rollback'
        assert sha(BACK/r['backup'])==r['before_sha256']
    for r in state['files']:replace(Path(r['path']),(BACK/r['backup']).read_bytes())
    state['state']='rolled-back';save(BACK/'installation.json',state);print('Rollback verified')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);a=p.parse_args();globals()[a.action]()
