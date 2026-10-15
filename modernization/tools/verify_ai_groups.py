"""Execute native recursive AI group iteration, including nested cursor limits."""
import json,struct
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA

def word(u,a):return struct.unpack('<I',u.mem_read(a,4))[0]

def group(u,address,children=(),unit=0,rank=0):
    u.mem_write(address,bytes(0x8d))
    u.mem_write(address+0x41,b'\1'*8)
    put(u,address+0x35,'I',unit);put(u,address+0x89,'i',rank)
    if children:
        array=address+0x100
        put(u,array,'I'*len(children),*children)
        put(u,address+0x29,'III',array,array+4*len(children),array+4*len(children))

def verify():
    cases=[]
    for entry,kind in [(0x4079f0,'units'),(0x407a80,'leaf_groups')]:
        for cutoff in [0,1,2,3]:
            u=machine();root=0x2010000;branch=root+0x400
            leaves=[root+0x800+i*0x400 for i in range(3)]
            for i,g in enumerate(leaves):group(u,g,unit=0x2020000+i*0x100,rank=i)
            group(u,branch,children=leaves[:2]);group(u,root,children=[branch,leaves[2]])
            put(u,0x5d854c,'i',cutoff)
            cursor=call(u,0x407920,root,[]);assert cursor==0
            actual=[]
            for _ in range(5):
                item=call(u,entry,root,[cursor])
                if not item:break
                actual.append(item)
            expected=[(0x2020000+i*0x100 if kind=='units' else leaves[i]) for i in range(3) if i>=cutoff]
            assert actual==expected,(kind,cutoff,actual,expected)
            assert bytes(u.mem_read(root+0x41+cursor,1))==b'\1'
            cases.append(dict(kind=kind,rank_cutoff=cutoff,returned=actual))
    # Independent reservations; exhausting all eight causes round-robin reuse.
    u=machine();g=0x2010000;group(u,g,unit=0x2020000);put(u,0x5d854c,'i',0)
    allocated=[call(u,0x407920,g,[]) for _ in range(11)]
    assert allocated==list(range(8))+[0,1,2]
    assert word(u,g+0x3d)==3
    cases.append(dict(kind='cursor_capacity',allocated=allocated,reuse='round_robin'))
    u=machine();g=0x2010000;group(u,g,unit=0x2020000);put(u,0x5d854c,'i',0)
    a=call(u,0x407920,g,[]);b=call(u,0x407920,g,[])
    assert call(u,0x4079f0,g,[a])==call(u,0x4079f0,g,[b])==0x2020000
    assert call(u,0x4079f0,g,[a])==0
    assert call(u,0x407920,g,[])==a
    assert call(u,0x4079f0,g,[a])==0x2020000
    cases.append(dict(kind='independent_cursors_and_reuse',cursors=[a,b]))
    # Direct-child iterator does not recurse; structural children survive cutoff.
    for cutoff in [0,2,3]:
        u=machine();root=0x2010000;branch=root+0x400;leaf=root+0x800
        group(u,branch);group(u,leaf,unit=0x2020000,rank=2)
        group(u,root,children=[branch,leaf]);put(u,0x5d854c,'i',cutoff)
        cursor=call(u,0x407920,root,[])
        actual=[]
        for _ in range(4):
            value=call(u,0x407990,root,[cursor])
            if not value:break
            actual.append(value)
        assert actual==[branch]+([leaf] if cutoff<=2 else [])
        cases.append(dict(kind='direct_children',rank_cutoff=cutoff,returned=actual))
    report=dict(engine_sha256=SHA,result='passed',cases=cases,scope='Real407920/407990/4079f0/407a80, nested synthetic groups, no stubs or game IO. Rank meaning not established by iterator tests.')
    (ROOT/'modernization/docs/ai-group-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
