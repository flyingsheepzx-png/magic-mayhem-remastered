"""Integrate verified FMV delivery into current isolated 1.1, without gameplay."""
import argparse,json,shutil,subprocess,os,time,ctypes
from pathlib import Path
import pefile
import build_remastered_11 as b
from install_11_minimap_v2 import idle,resources

DELIVERY=b.ROOT/'modernization/assets/fmv-delivery-1440p-20261001'
OUT=b.ROOT/'modernization/build/remastered-1.1-fmv-h264'
BACK=b.ROOT/'modernization/backups/remastered-1.1-fmv-h264'
RT=b.TARGET/'runtime'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
MANIFEST=b.TARGET/'manifest.json'
FILMS=('Medieval','Intro1','intro0','Celtic','Greek')

def replace(path,raw):
    temp=path.with_name(path.name+'.fmv-install.tmp')
    assert not temp.exists(), 'Unresolved FMV temporary file'
    temp.write_bytes(raw)
    try:
        for attempt in range(16):
            try:
                if path.exists():
                    k=ctypes.WinDLL('kernel32',use_last_error=True)
                    k.ReplaceFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_void_p]
                    if not k.ReplaceFileW(str(path),str(temp),None,0,None,None):raise ctypes.WinError(ctypes.get_last_error())
                else:os.replace(temp,path)
                return
            except PermissionError:
                if attempt==15:raise
                time.sleep(.2)
    finally:
        if temp.exists():temp.unlink()

def delivery():
    player=json.loads((DELIVERY/'player-build.json').read_text(encoding='utf-8'))
    m=json.loads((DELIVERY/'manifest.json').read_text(encoding='utf-8'))
    assert player['engine_sha256']==b.sha(RT/'Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
    assert b.sha(DELIVERY/'fmv_h264.dll')==player['dll_sha256']=='9b86df83d71198afe02474fbeae5380f55da99746cc051e6ac169d9263108789'
    assert b.sha(DELIVERY/'FMV-1440p-Playtest.exe')==player['launcher_sha256']
    for name in FILMS:
        r=m['films'][name];assert r['verified'] and Path(r['mp4']).resolve()==(DELIVERY/(name+'.mp4')).resolve()
        assert b.sha(DELIVERY/(name+'.mp4'))==r['mp4_sha256']
        assert (DELIVERY/(name+'.mp4')).stat().st_size==r['bytes']
    return player,m

def run(action):
    idle();b.verify()
    if action=='rollback':
        state=json.loads((BACK/'installation.json').read_text(encoding='utf-8'))
        for r in state['files']:
            assert b.sha(b.TARGET/r['path'])==r['installed_sha256']
            if r['before_sha256'] is not None:assert b.sha(BACK/r['path'])==r['before_sha256']
        for r in state['files']:
            p=(b.TARGET/r['path']).resolve();assert p.is_relative_to(b.TARGET.resolve())
            if r['before_sha256'] is None:p.unlink()
            else:
                old=BACK/r['path'];assert b.sha(old)==r['before_sha256'];replace(p,old.read_bytes())
        b.verify();print('Rolled back FMV integration; saves and preferences retained');return
    player,m=delivery()
    if action=='build':
        OUT.mkdir(exist_ok=False)
        # A source-only FMV delta: reversing it must recover current launcher
        # source exactly. The embedded current modules are extracted, not rebuilt.
        source=(DELIVERY/'launcher.cpp').read_text(encoding='utf-8')
        current=(b.ROOT/'modernization/build/remastered-1.1-teammate-portrait/launcher.cpp').read_text(encoding='utf-8')
        start=source.index('    void* gate=');end=source.index('    wchar_t temp[MAX_PATH];',start)
        recovered=source[:start]+source[end:]
        recovered=recovered.replace('    SetEnvironmentVariableW(L"MM_FMV_H264",L"1");\n','')
        recovered=recovered.replace('FALSE,CREATE_SUSPENDED,nullptr,game.c_str()','FALSE,0,nullptr,game.c_str()')
        assert recovered==current,'Unexpected stale launcher changes'
        engine=pefile.PE(str(RT/'Chaos-Wide169-engine.exe'))
        assert engine.OPTIONAL_HEADER.ImageBase+engine.OPTIONAL_HEADER.AddressOfEntryPoint==0x5c4090
        assert engine.get_data(0x469a00-0x400000,6)==bytes.fromhex('518d44240056')
        before=resources(ENTRY);assert set(before)=={101,102}
        for key,name in [(101,'repath.dll'),(102,'qol_bindings.dll')]:
            assert before[key]==(b.ROOT/'modernization/build/remastered-1.1-teammate-portrait'/name).read_bytes()
            (OUT/name).write_bytes(before[key])
        for name in ['fmv_h264.cpp','fmv_h264.dll']:shutil.copy2(DELIVERY/name,OUT/name)
        (OUT/'launcher.cpp').write_text(source,encoding='utf-8')
        (OUT/'combined.rc').write_text('101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n')
        cmd=(DELIVERY/'build-launcher.cmd').read_text().replace('FMV-1440p-Playtest.exe',ENTRY.name)
        (OUT/'build.cmd').write_text(cmd)
        subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True,timeout=120)
        assert resources(OUT/ENTRY.name)==before
        assert b.sha(OUT/'fmv_h264.dll')==player['dll_sha256']
        # Existing module allowlists remain pinned to currently installed files.
        for name in ['jpeg.dll','jpeg_native.dll','png_assets.dll','terrain_diagonal.dll','png_pages.dll']:
            assert b.sha(RT/name) in source
        films=[dict(path='FMV/'+name+'.mp4',sha256=m['films'][name]['mp4_sha256'],
                    bytes=m['films'][name]['bytes'],method=m['films'][name]['method']) for name in FILMS]
        b.write(OUT/'verification.json',dict(result='passed',films=films,dll_sha256=player['dll_sha256'],
            launcher_before_sha256=b.sha(ENTRY),manifest_before_sha256=b.sha(MANIFEST),
            launcher_sha256=b.sha(OUT/ENTRY.name),resources_preserved={str(k):__import__('hashlib').sha256(v).hexdigest() for k,v in before.items()},
            source_hashes={n:b.sha(OUT/n) for n in ['launcher.cpp','fmv_h264.cpp']},
            delivery_manifest_sha256=b.sha(DELIVERY/'manifest.json'),
            validation='delivery playback evidence reused; installed campaign trigger acceptance pending'))
    else:
        v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
        assert v['result']=='passed'
        assert b.sha(ENTRY)==v['launcher_before_sha256'] and b.sha(MANIFEST)==v['manifest_before_sha256']
        assert b.sha(OUT/ENTRY.name)==v['launcher_sha256']
        assert resources(OUT/ENTRY.name)==resources(ENTRY)
        assert b.sha(OUT/'fmv_h264.dll')==v['dll_sha256']
        assert b.sha(DELIVERY/'manifest.json')==v['delivery_manifest_sha256']
        for n,h in v['source_hashes'].items():assert b.sha(OUT/n)==h
        runtime_before=b.inventory(RT)
        # A failed first-file rename leaves only exact backups, no install state.
        if BACK.exists():
            assert not (BACK/'installation.json').exists()
            assert b.sha(BACK/ENTRY.name)==b.sha(ENTRY)
            assert b.sha(BACK/'manifest.json')==b.sha(MANIFEST)
        else:BACK.mkdir()
        updates={ENTRY:(OUT/ENTRY.name).read_bytes(),RT/'fmv_h264.dll':(OUT/'fmv_h264.dll').read_bytes()}
        for row in v['films']:
            assert b.sha(DELIVERY/Path(row['path']).name)==row['sha256']
            updates[RT/row['path']]=(DELIVERY/Path(row['path']).name).read_bytes()
        package=json.loads(MANIFEST.read_text(encoding='utf-8'));package['launcher_sha256']=v['launcher_sha256']
        package['fmv_h264']=dict(verification=v,backup=str(BACK),fallback='preserved native AVI',
            scope='isolated1.1 only',acceptance='installed user playback and campaign triggers pending')
        package['files']['fmv_h264.dll']=v['dll_sha256']
        for row in v['films']:package['files'][row['path']]=row['sha256']
        updates[MANIFEST]=(json.dumps(package,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        before={p:p.read_bytes() if p.exists() else None for p in updates}
        records=[]
        for p,raw in before.items():
            rel=p.relative_to(b.TARGET).as_posix();backup=BACK/rel
            if raw is not None:backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(raw)
            records.append(dict(path=rel,before_sha256=b.sha(p) if raw is not None else None,
                installed_sha256=__import__('hashlib').sha256(updates[p]).hexdigest()))
        try:
            for p,raw in updates.items():p.parent.mkdir(parents=True,exist_ok=True);replace(p,raw)
            expected=dict(runtime_before);expected['fmv_h264.dll']=v['dll_sha256']
            for row in v['films']:expected[row['path']]=row['sha256']
            assert b.inventory(RT)==expected, 'Unrelated runtime/config/save changed'
            b.verify()
        except BaseException:
            for p,raw in before.items():
                if raw is None:p.unlink(missing_ok=True)
                elif not p.exists() or p.read_bytes()!=raw:replace(p,raw)
            raise
        b.write(BACK/'installation.json',dict(files=records))
    print(action,'FMV H.264 integration passed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);run(p.parse_args().action)
