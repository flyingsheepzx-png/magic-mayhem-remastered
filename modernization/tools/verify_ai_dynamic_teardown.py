"""Actual retirement suffix428e00 calls base cleanup, not prototype teardown."""
import json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(row,populated=False,use_factory=False):
    u=machine();u.mem_map(0,0x1000)
    for p in range(0x5faf20,0x5faf4c,4):put(u,p,'I',0)
    allocations={};released=set();bump=[0x2200000];calls=[]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def inspect(uc,address,size,user):
        if address==0x418050:calls.append('base418050')
        elif address==0x597850:
            n=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
            ptr=bump[0];bump[0]+=(n+15)&~15;allocations[ptr]=n
            uc.reg_write(UC_X86_REG_EAX,ptr)
        elif address==0x597870:
            ptr=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
            if ptr:
                assert ptr in allocations and ptr not in released
                released.add(ptr)
    u.hook_add(UC_HOOK_CODE,inspect)
    if use_factory:
        a=call(u,int(row['methods']['clone'],16),0x2010000,[])
        assert a in allocations
    else:
        a=call(u,0x597850,0,[0x400])
        assert call(u,int(row['constructor'],16),a,[])==a
    additional=[]
    if populated and row['action_id']==6:
        for offset in [0x163,0x17f]:
            ptr=call(u,0x597850,0,[16]);additional.append(ptr)
            put(u,ptr,'4I',1,2,3,4);put(u,a+offset,'3I',ptr,ptr+16,ptr+16)
    u.reg_write(UC_X86_REG_ESI,a);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x428e00,0x428e14,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x428e14 and calls==['base418050']
    assert a in released
    remaining={hex(p):n for p,n in allocations.items() if p not in released}
    if row['action_id']==12:assert sorted(remaining.values())==[20,20]
    elif populated:
        assert set(remaining)=={hex(p) for p in additional}
    else:assert not remaining
    return dict(action_id=row['action_id'],populated_tactical_vectors=populated,use_native_factory=use_factory,
                allocation_count=len(allocations),released_count=len(released),
                remaining_allocations=remaining,called=calls)

def verify():
    rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
    cases=[fixture(row) for row in rows]
    cases.append(fixture(next(row for row in rows if row['action_id']==6),True))
    cases.extend(fixture(row,use_factory=True) for row in rows)
    report=dict(engine_sha256=SHA,result='passed',cases=cases,
                scope='Exact retirement428e00..428e14 native suffix,all53 constructors and all53 native fresh-instance factories,real base418050; CRT allocation/free sinks only. Retreat extra trees persist through factory-to-deletion path;synthetic AggressiveAttack vectors persist. Earlier retirement/map/group phases and full gameplay lifecycle not exercised;not quantified production leak frequency.')
    (ROOT/'modernization/docs/ai-dynamic-teardown-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),retained_cases=sum(bool(c['remaining_allocations']) for c in cases)))

if __name__=='__main__':verify()
