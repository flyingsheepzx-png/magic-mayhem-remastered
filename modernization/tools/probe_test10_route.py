"""Read-only, no-order replay of test10 on the installed wide169 identity."""
import ctypes
import json
import struct
import time
import os
from ctypes import wintypes as W
from wide169_trial import Session, ROOT, GAME, LAB, sha
from verify_hd60_runtime import read


def main():
    identity = json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']
    installed = json.loads((ROOT/'modernization/wide169-installed.json').read_text())
    manifest = __import__('pathlib').Path(installed['package'])/'manifest.json'
    assert sha(manifest.read_bytes()) == installed['manifest_sha256']
    package = json.loads(manifest.read_text())
    for name in ('game/Chaos-Wide169-Trial.exe', 'game-wide169/Chaos-Wide169-engine.exe'):
        expected=identity['files'][name]
        assert sha((ROOT/name).read_bytes()) == expected, name
    assert package['launcher_sha256'] == identity['files']['game/Chaos-Wide169-Trial.exe']
    assert package['engine_sha256'] == identity['files']['game-wide169/Chaos-Wide169-engine.exe']
    fixture = LAB/'Save/test10.sav'
    with Session() as s:
        # Persist mutable backups before loading a gameplay fixture.
        backup = s.run/'mutable'; backup.mkdir()
        for p, (data, _, _) in s.mutable.items():
            dst = backup/p.relative_to(LAB); dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(data)
        s.result['fixture_sha256'] = sha(fixture.read_bytes())
        s.result['identity'] = identity
        s.k.QueryFullProcessImageNameW.argtypes = [W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
        size=W.DWORD(32768); path=ctypes.create_unicode_buffer(size.value)
        assert s.k.QueryFullProcessImageNameW(s.handle,0,path,ctypes.byref(size))
        assert __import__('pathlib').Path(path.value).resolve() == (LAB/'Chaos-Wide169-engine.exe').resolve()
        s.capture('after-intro-skip')
        s.result['menu_controls']=s.controls()
        s.click(640,456); time.sleep(.7)
        s.capture('load-dialog')
        rows=sorted((LAB/'Save').glob('*.sav'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
        n=[p.stem.lower() for p in rows].index('test10')
        assert n < 10
        s.click(640,292+n*24); time.sleep(.2)
        s.click(328,666)
        started=time.perf_counter(); samples=[]; last=None; map_saved=False; captures=set()
        while time.perf_counter()-started < 18:
            t=time.perf_counter()-started
            base=s.i(0x6def58); count=s.i(0x6df180); capacity=s.i(0x6def5c)
            if base and 0<count<=capacity<=1024:
                blob=read(s.k,s.handle,base,0xe4b)
                val=lambda off: struct.unpack_from('<i',blob,off)[0]
                grid=[val(o) for o in (8,12,16)]
                dims=[s.i(a) for a in (0x6c5494,0x6c5498,0x6c549c)]
                if val(4) and all(0<=x<d for x,d in zip(grid,dims)):
                    state=dict(grid=grid,world=[val(o) for o in (0x14,0x18,0x1c)],
                               active=val(0x618),route=blob[0x96b:0x96b+0x20c].hex())
                    if state!=last:
                        samples.append(dict(seconds=t,**state)); last=state
                    if not map_saved:
                        cells=s.i(0x6c54dc)
                        assert 0 < dims[0]*dims[1]*dims[2] <= 4000000
                        (s.run/'map.bin').write_bytes(read(s.k,s.handle,cells,12*dims[0]*dims[1]*dims[2]))
                        (s.run/'unit0.bin').write_bytes(blob)
                        tile_table=s.i(0x65660c)
                        # Bound the export by the largest tile ID in this map.
                        raw_map=(s.run/'map.bin').read_bytes()
                        tile_count=max(struct.unpack_from('<H',raw_map,j)[0] for j in range(0,len(raw_map),12))+1
                        assert 0 < tile_count < 4096
                        (s.run/'tile-types.bin').write_bytes(read(s.k,s.handle,tile_table,0x164*tile_count))
                        (s.run/'unit-type.bin').write_bytes(read(s.k,s.handle,val(0xac),0x100))
                        s.result['map_dimensions']=dims
                        map_saved=True
                        print('Loaded',grid,'goal',[val(o) for o in (0x96b,0x96f,0x973)],flush=True)
                    bucket=int(t)//5
                    if bucket not in captures:
                        s.capture('route-'+str(bucket)); captures.add(bucket)
            time.sleep(.015)
        (s.run/'route.json').write_text(json.dumps(samples),encoding='utf-8')
        s.result['samples']=len(samples)
        s.result['no_gameplay_orders']=True
        if not samples:
            s.capture('failed-load')
            raise RuntimeError('No live fixture sampled; load did not complete')
        print('Route',str(s.run),len(samples),flush=True)


if __name__ == '__main__':
    from verify_hd60_runtime import configured_kernel, processes
    if any(name.startswith('chaos') for _,_,name in processes(configured_kernel())):
        raise RuntimeError('Game already running')
    prefs=LAB/'CFG/prefs.cfg'; original=prefs.read_bytes(); stat=prefs.stat()
    backup=ROOT/'modernization/backups/test10-route'/str(time.time_ns())
    backup.mkdir(parents=True)
    (backup/'prefs.cfg').write_bytes(original)
    try:
        assert b'PlayFMV=TRUE' in original
        prefs.write_bytes(original.replace(b'PlayFMV=TRUE',b'PlayFMV=FALSE'))
        main()
    finally:
        prefs.write_bytes(original)
        os.utime(prefs,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        assert prefs.read_bytes()==original
