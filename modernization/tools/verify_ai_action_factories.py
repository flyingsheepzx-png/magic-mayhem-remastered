"""Registered 'clone' slot is a fresh-instance factory, not a state copy."""
import json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_action_construction import cleanup_map
from verify_ai_model_native import ROOT,SHA

def fixture(row,cleanup,fail=False):
    u=machine();u.mem_map(0,0x1000)
    for p in range(0x5faf20,0x5faf4c,4):put(u,p,'I',0)
    source=0x2010000;before=bytes((i*37+11)%256 for i in range(0x800))
    u.mem_write(source,before)
    allocations={};released=set();bump=[0x2200000];attempts=[]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def inspect(uc,address,size,user):
        n=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
        if address==0x597850:
            attempts.append(n)
            if fail:
                assert len(attempts)==1
                uc.reg_write(UC_X86_REG_EAX,0);return
            ptr=bump[0];bump[0]+=(n+15)&~15
            allocations[ptr]=n;uc.reg_write(UC_X86_REG_EAX,ptr)
        elif address==0x597870 and n:
            assert n in allocations and n not in released
            released.add(n)
    u.hook_add(UC_HOOK_CODE,inspect)
    result=call(u,int(row['methods']['clone'],16),source,[])
    assert bytes(u.mem_read(source,len(before)))==before
    if fail:
        assert result==0 and not allocations
        assert all(word(u,p)==0 for p in range(0x5faf20,0x5faf4c,4))
    else:
        assert result in allocations and result!=source
        assert word(u,result)==int(row['vtable'],16)
        assert word(u,result+4)==row['action_id'] and word(u,result+0x23)==0xffffffff
        assert all(word(u,result+o)==0 for o in [0x3b,0x3f,0x43])
        call(u,int(cleanup['cleanup'],16),result,[])
        # Prototype cleanup does not free the object storage itself.
        assert set(allocations)-released=={result}
        call(u,0x597870,0,[result]);assert released==set(allocations)
    return dict(action_id=row['action_id'],factory=row['methods']['clone'],
                object_size=attempts[0],first_allocation_failed=fail,
                returned_null=result==0,allocation_count=len(allocations))

def verify():
    rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
    mapping=cleanup_map(rows)
    cases=[fixture(row,mapping[row['action_id']],fail) for row in rows for fail in [False,True]]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='All53 native clone-slot factories,success and first object-allocation failure. Arbitrary source bytes untouched; fresh ID/vtable/sample/owned-vector initialized. Matching derived cleanup plus explicit storage free matches every allocation. CRT allocation/free sinks only. Nested allocation failure/exception unwinding and all field defaults pending.')
    (ROOT/'modernization/docs/ai-action-factory-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
