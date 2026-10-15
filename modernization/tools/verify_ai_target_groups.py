"""Native own-owner and visible-allied target group construction."""
import itertools,json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(entry,mask,owner=2):
    u=machine();a=0x2100000;pool=0x2010000
    specs=list(itertools.product([1,2,3],[0,1],[0,1],[0,1],[1,27]))
    put(u,0x6def58,'I',pool);put(u,0x6df180,'I',len(specs))
    for i,(team,active,health,seen,kind) in enumerate(specs):
        p=pool+i*0xe4b
        put(u,p+4,'I',active);put(u,p+0xe4,'I',health)
        put(u,p+0x174,'I',team);put(u,p+0xa8,'I',kind)
        put(u,p+0x24+2*4,'I',seen)
    for team in [1,2,3]:put(u,0x643a80+2*0x154+0x18+team,'B',bool(mask&(1<<(team-1))))
    allocations=[];freed=[];bump=[0x2200000]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def allocator(uc,address,size,user):
        n=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
        if address==0x597850:
            ptr=bump[0];bump[0]+=(n+15)&~15
            assert bump[0]<0x23e0000
            allocations.append(n);uc.reg_write(UC_X86_REG_EAX,ptr)
        elif address==0x597870:freed.append(n)
    u.hook_add(UC_HOOK_CODE,allocator)
    root=call(u,entry,a,[owner&0xffffffff])
    expected=[]
    for i,(team,active,health,seen,kind) in enumerate(specs):
        eligible=active and health and (team==owner if entry==0x40f910 else
                    owner==2 and seen and kind!=27 and mask&(1<<(team-1)))
        if eligible:expected.append(pool+i*0xe4b)
    begin=word(u,root+0x29);end=word(u,root+0x2d)
    assert (end-begin)//4==len(expected)
    children=[word(u,begin+4*i) for i in range(len(expected))]
    assert [word(u,c+0x35) for c in children]==expected
    assert all(word(u,c+0x39)==root for c in children)
    assert all(word(u,c+0x89)==3 for c in children)
    ownedbegin=word(u,a+0x3b);ownedend=word(u,a+0x3f)
    owned=[word(u,ownedbegin+4*i) for i in range((ownedend-ownedbegin)//4)]
    assert owned==[root]+children
    assert call(u,0x4078a0,root,[])==len(expected)
    assert bytes(u.mem_read(root+0x41,8))==b'\1'*8
    return dict(builder=hex(entry),alliance_mask=mask,observer_owner=owner,
                input_units=len(specs),target_units=expected,allocation_sizes=allocations,
                freed_buffers=len(freed))

def verify():
    cases=[fixture(entry,mask) for entry,mask in itertools.product([0x40f910,0x40f9e0],range(8))]
    cases.extend(fixture(0x40f9e0,7,owner) for owner in [-1,8])
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='Full40f910/40f9e0,419990/419a10 constructors,52a710 with real412aa0, vector insertion and4078a0. Only CRT allocation/free doubled.48 synthetic units per fixture prove active/living/owner/visibility/type/alliance filtering, ordering, parents and action ownership. Native alliance/visibility producers and destruction remain pending.')
    (ROOT/'modernization/docs/ai-target-group-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
