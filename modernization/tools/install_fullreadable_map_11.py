"""Install/rollback only the user-selected Full Readable Celtic map in 1.1."""
from pathlib import Path
import argparse,json,hashlib,io,os,shutil,subprocess
from PIL import Image,ImageChops
import build_remastered_11 as b
REL='Interface/RealmViewer/800x600/Celtic_Map.PNG'
SOURCE=b.ROOT/'modernization/assets/hd/quality-review-1.1/model-trials/02-full-readable-target.png'
TRIAL=SOURCE.parent
BACK=b.ROOT/'modernization/backups/remastered-1.1-fullreadable-celtic'
MANIFEST=b.TARGET/'manifest.json'
EXPECTED_SOURCE='e3ffa2c938e5fbd110fc3315b336fb8cd1eb362d5c86c9e571caa6792c700a9c'
EXPECTED_OLD='f2d1906ac724e5f0954ff0216891b1797aebbc64416e853dc2200b884d4c5d6b'
def idle():
    from verify_hd60_runtime import configured_kernel,processes
    if any(n.startswith('chaos') for _,_,n in processes(configured_kernel())):
        raise RuntimeError('Close the game before replacing the map')
def save(path,data):
    temp=path.with_name(path.name+'.fullreadable.tmp')
    if temp.exists():raise RuntimeError('Unresolved staging file: '+str(temp))
    temp.write_bytes(data);os.replace(temp,path)
def install():
    raise RuntimeError('FullReadable generation retired by user; use SeedVR2 production. Historical rollback remains available.')
    idle();b.verify()
    if BACK.exists():raise RuntimeError('Keep existing backup; replacement already staged')
    index=json.loads((TRIAL/'artifact-index.json').read_text(encoding='utf-8'))
    record=next(x for x in index if x['file']==SOURCE.name)
    assert record['sha256']==EXPECTED_SOURCE and b.sha(SOURCE)==EXPECTED_SOURCE
    target=b.TARGET/'runtime'/REL;old=target.read_bytes();assert hashlib.sha256(old).hexdigest()==EXPECTED_OLD
    manifest_bytes=MANIFEST.read_bytes();m=json.loads(manifest_bytes)
    assert m['files'][REL]==EXPECTED_OLD
    before=b.inventory(b.TARGET/'runtime')
    with Image.open(SOURCE) as opened:
        assert opened.format=='PNG' and opened.size==(1920,1440)
        src=opened.convert('RGB');canvas=Image.new('RGB',(2560,1440),(0,0,0));canvas.paste(src,(320,0))
        data=io.BytesIO();canvas.save(data,format='PNG',compress_level=6);new=data.getvalue()
    with Image.open(io.BytesIO(new)) as check:
        assert check.size==(2560,1440)
        assert ImageChops.difference(check.crop((320,0,2240,1440)),src).getbbox() is None
        assert check.crop((0,0,320,1440)).getbbox() is None
        assert check.crop((2240,0,2560,1440)).getbbox() is None
    BACK.mkdir(parents=True);(BACK/'Celtic_Map.PNG').write_bytes(old);(BACK/'manifest.json').write_bytes(manifest_bytes)
    digest=hashlib.sha256(new).hexdigest()
    update=dict(variant='02-full-readable',source_sha256=EXPECTED_SOURCE,installed_sha256=digest,previous_sha256=EXPECTED_OLD,content_origin=[320,0],native_content=[1920,1440],canvas=[2560,1440],backup=str(BACK),acceptance='pending user gameplay testing',scope='Celtic realm only; same filename; existing overlays/hitmask')
    m['files'][REL]=digest;m['fullreadable_celtic']=update
    try:
        save(target,new);save(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        assert b.sha(target)==digest
        after=b.inventory(b.TARGET/'runtime')
        assert set(after)==set(before)
        assert [n for n in before if before[n]!=after[n]]==[REL]
        b.verify()
    except BaseException:
        save(target,old);save(MANIFEST,manifest_bytes);raise
    b.write(BACK/'installation.json',dict(**update,asset=REL,changed_runtime_files=[REL],pixel_check='exact source content at 1:1; both 320px sidebars black',gameplay_started=False))
    print(json.dumps(update,ensure_ascii=False,indent=2))
def rollback():
    idle();b.verify()
    report=json.loads((BACK/'installation.json').read_text(encoding='utf-8'));target=b.TARGET/'runtime'/REL
    assert b.sha(target)==report['installed_sha256']
    assert b.sha(BACK/'Celtic_Map.PNG')==EXPECTED_OLD
    old_manifest=json.loads((BACK/'manifest.json').read_text(encoding='utf-8'));current=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert current['files'][REL]==report['installed_sha256']
    # Retain any later unrelated candidate metadata; change only this asset entry.
    current['files'][REL]=old_manifest['files'][REL];current.pop('fullreadable_celtic',None)
    save(target,(BACK/'Celtic_Map.PNG').read_bytes());save(MANIFEST,(json.dumps(current,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    b.verify();print('Previous Celtic map restored; player saves/configuration retained.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);globals()[p.parse_args().action]()
