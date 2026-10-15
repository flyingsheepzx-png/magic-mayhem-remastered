"""Whole4656c0: named-profile counter and symmetric relation break."""
import itertools,json,struct
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word
from unicorn.x86_const import UC_X86_REG_ESP

def fixture(src,dst,named,relation=1,immune=0,old=99,delta=1,lowercase=False):
    u=machine();u.mem_write(BASE,b'\xa5'*SIZE);put(u,0x5fbf28,'I',BASE)
    for i in range(8):
        label=('cornelius' if lowercase else 'Cornelius') if i==named else f'P{i}'
        u.mem_write(BASE+i*0x154+0x50,label.encode()+b'\0')
    put(u,BASE+src*0x154+0x18+dst,'B',relation)
    put(u,BASE+src*0x154+0x28+dst,'B',immune)
    put(u,BASE+src*0x154+0x30+4*dst,'I',old&0xffffffff)
    expected=bytearray(u.mem_read(BASE,SIZE))
    admitted=src!=dst and relation!=0 and immune==0 and not lowercase and (src==named or dst==named)
    if admitted:
        total=((old+delta+2**31)%2**32)-2**31
        word(expected,src*0x154+0x30+4*dst,total)
        if total>=100:
            expected[src*0x154+0x18+dst]=0;expected[dst*0x154+0x18+src]=0
    call(u,0x4656c0,BASE+src*0x154,[delta&0xffffffff,dst])
    actual=bytes(u.mem_read(BASE,SIZE))
    assert actual==expected,(src,dst,named,old,delta,[(hex(i),actual[i],expected[i]) for i in range(SIZE) if actual[i]!=expected[i]][:12])
    assert u.reg_read(UC_X86_REG_ESP)==0x23f000c
    return dict(src=src,dst=dst,named=named,relation=relation,immune=immune,old=old,delta=delta,lowercase=lowercase,admitted=admitted)

def verify():
    pairs=[fixture(*v) for v in itertools.product(range(8),range(8),range(-1,8))]
    gates=[fixture(*v) for v in itertools.product((0,3,7),(0,3,7),(-1,0,3,7),(0,1),(0,1),(-1,0,99,100,2147483647),(-1,1,100))]
    cases=pairs+gates+[fixture(0,1,n,lowercase=True) for n in (-1,0,1)]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='2739 whole4656c0 no-double calls. All8x8pairs/9uniqueCorneliusplacements inclnone,selectedgate/countermatrix andlowercase mismatch. Exact case-sensitiveCornelius match5d96f4;source match or targetfirstmatchingglobalprofile required. Self/relation18zero/immunity28nonzero no-op. Otherwisewrappedsource30[dst]+=delta;signedtotal>=100 clears18bothdirections. Fullaa8snapshots/ret8. Name label semantics,eventcaller/delta units,duplicates/invalidindex/globalalias andother20/28writers/save/network pending.')
    (ROOT/'modernization/docs/ai-relation-counter-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),admitted=sum(c['admitted'] for c in cases)))

if __name__=='__main__':verify()
