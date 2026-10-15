"""Explain the two flat diagonal candidates from read-only test10 snapshots.

The clearance predicate is the observed 0x4f3440 algorithm, for the saved
single-cell walking wizard. It is not a replacement path planner.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import pefile

ROOT=Path(__file__).resolve().parents[2]


def analyze(run):
    report=json.loads((run/'result.json').read_text())
    assert report['status']=='completed' and not report['changed_protected']
    dims=report['map_dimensions']; raw=(run/'map.bin').read_bytes()
    tiles=(run/'tile-types.bin').read_bytes(); unit=(run/'unit0.bin').read_bytes()
    typ=(run/'unit-type.bin').read_bytes()
    height=struct.unpack_from('<i',typ,12)[0]
    assert struct.unpack_from('<i',typ,8)[0]==1
    assert struct.unpack_from('<i',unit,0x104)[0]==0
    original=ROOT/'game/Chaos.exe'; current=ROOT/'game-wide169/Chaos-Wide169-engine.exe'
    assert hashlib.sha256(original.read_bytes()).hexdigest()=='b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291'
    assert hashlib.sha256(current.read_bytes()).hexdigest()==report['engine_sha256']
    old,new=pefile.PE(str(original)),pefile.PE(str(current))
    spans=[(0x4f3320,0x28c0),(0x514360,0x2d0)]
    identical=all(old.get_data(a-0x400000,n)==new.get_data(a-0x400000,n) for a,n in spans)
    assert identical

    def cell(x,y,z):
        assert all(0<=v<d for v,d in zip((x,y,z),dims))
        tile,obj,owner,a,b,flags=struct.unpack_from('<6H',raw,12*(x+y*dims[0]+z*dims[0]*dims[1]))
        kind=struct.unpack_from('<I',tiles,tile*0x164+0x94)[0] if tile else 0
        return dict(x=x,y=y,z=z,tile=tile,tile_kind=kind,object_id=obj,unit_id=owner,flags=hex(flags))

    def clearance(pos):
        x,y,z=pos; cells=[cell(x,y,z+k) for k in range(height)]
        for k,c in enumerate(cells):
            flags=int(c['flags'],16)
            reason=None
            if flags & 0x4000: reason='solid-volume flag 0x4000'
            elif c['tile'] and not flags&0x80 and (k>0 or c['tile_kind']==16):
                reason='solid tile in headroom' if k else 'blocking base tile kind 16'
            elif flags&0x30 and not flags&0x10: reason='native terrain flag restriction'
            if reason:return dict(clear=False,reason=reason,blocking_cell=c,cells=cells)
        return dict(clear=True,cells=cells)

    cases=[]
    for label,a,b in [('start',[58,78,4],[57,77,4]),('near-portal',[54,74,5],[53,73,5])]:
        sides=[[a[0],b[1],a[2]],[b[0],a[1],a[2]]]
        cases.append(dict(label=label,source=a,target=b,target_clearance=clearance(b),
                          side_clearance=[dict(position=p,**clearance(p)) for p in sides]))
    samples=json.loads((run/'route.json').read_text()); grid=[]
    for s in samples:
        if not grid or grid[-1]['grid']!=s['grid']:
            grid.append(dict(seconds=round(s['seconds'],3),grid=s['grid']))
    result=dict(fixture_sha256=report['fixture_sha256'],engine_sha256=report['engine_sha256'],
                native_spans_identical_to_community=identical,
                verified_spans=[dict(va=hex(a),size=n,sha256=hashlib.sha256(new.get_data(a-0x400000,n)).hexdigest()) for a,n in spans],
                wizard_height=height,cases=cases,observed_grid_transitions=grid,
                interpretation='Offline native-clearance reconstruction; no live function call or memory write',
                no_gameplay_orders=report['no_gameplay_orders'])
    (run/'diagonal-analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run',type=Path)
    analyze(parser.parse_args().run)
