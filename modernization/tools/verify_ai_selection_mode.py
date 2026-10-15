"""Native mode selection with explicit profile predicate and RNG doubles."""
import itertools,json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA

def fixture(policy,game_kind,eligible,threshold,rng,previous,real_profile=False):
    u=machine();m=0x2010000;sp=0x23f0000
    put(u,0x5d8650,'i',policy);put(u,0x689920,'i',game_kind)
    put(u,0x689924,'i',2);put(u,0x6e200c+8,'i',threshold)
    put(u,m+0x11ddc,'B',previous);put(u,sp+0x5c,'I',3)
    if real_profile:
        for slot in range(8):put(u,0x643a80+slot*0x154,'II',0,0)
        put(u,0x643a80+7*0x154,'II',int(eligible),1)
        put(u,0x643a80+7*0x154+0x18+3,'B',0)
    else:u.mem_write(0x466980,b'\xc2\x04\x00')
    u.mem_write(0x54e200,b'\xc3')
    seen=[]
    def capture(uc,address,size,user):
        if address==0x466980:
            seen.append('profile')
            if not real_profile:uc.reg_write(UC_X86_REG_EAX,int(eligible))
        elif address==0x54e200:seen.append('rng');uc.reg_write(UC_X86_REG_EAX,rng)
    u.hook_add(UC_HOOK_CODE,capture)
    u.reg_write(UC_X86_REG_EBX,m);u.reg_write(UC_X86_REG_ESP,sp)
    u.emu_start(0x4239e6,0x423a65,count=10000)
    assert u.reg_read(UC_X86_REG_EIP)==0x423a65
    expected=0 if policy==0 else 1 if policy==2 else previous
    calls=[]
    if policy==1:
        expected=0
        if game_kind not in (1,2):
            calls.append('profile')
            if eligible:
                calls.append('rng');expected=int((rng&0x7fffffff)%100<threshold)
    actual=bytes(u.mem_read(m+0x11ddc,1))[0]
    assert actual==expected and seen==calls,(actual,expected,seen,calls)
    return dict(policy=policy,game_kind=game_kind,eligible=eligible,threshold=threshold,rng=rng,previous=previous,mode=actual,calls=seen,real_profile=real_profile)

def verify():
    cases=[fixture(*v) for v in itertools.product([-1,0,1,2,3],[0,1,2,3],[False,True],[-1,0,50,100,101],[0,49,50,99,0xffffffff],[0,1])]
    cases.extend(fixture(*v,real_profile=True) for v in itertools.product([-1,0,1,2,3],[0,1,2,3],[False,True],[-1,0,50,100,101],[0,49,50,99,0xffffffff],[0,1]))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Native4239e6..423a65 mode decision:2000 predicate-double cases plus2000 real466980 cases.54e200 RNG explicit double throughout. Config5d8650,game kind689920,index689924 and indexed threshold6e200c. Symbol names/config mapping/profile+4 meaning and full scheduler remain pending.')
    (ROOT/'modernization/docs/ai-selection-mode-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
