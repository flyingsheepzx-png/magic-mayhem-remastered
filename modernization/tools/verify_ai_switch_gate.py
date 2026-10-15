"""Native current-action replacement gate, before candidate offset/selection."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_resource_value import ext
from verify_ai_model_native import ROOT,SHA
from verify_ai_retirement import setup
from verify_ai_outcome_ratio import expected_ratio

def fixture(candidate,current,free_switch,protected,ratio,elapsed,present=True,world=None):
    candidate=struct.unpack('<f',struct.pack('<f',candidate))[0]
    current=struct.unpack('<f',struct.pack('<f',current))[0]
    if world is None:
        u=machine();old=0x2050000
    else:
        u,old,*_=setup(*world)
        ratio=expected_ratio(*world)
    m=0x2080000;frame=0x2090000
    put(u,frame+8,'f',candidate);put(u,frame+0x14,'I',old if present else 0)
    put(u,m+0x14,'I',100+elapsed)
    put(u,old+0x15,'B',free_switch);put(u,old+0x1a,'B',protected)
    put(u,old+0x1b,'f',current);put(u,old+0xc,'II',100,110)
    put(u,0x2060000,'d',ratio)
    # Recovered outcome ratio is independently verified; isolate gate from world.
    if world is None:u.mem_write(0x40a3b0,b'\xdd\x05'+struct.pack('<I',0x2060000)+b'\xc3')
    boundaries=[]
    def inspect(uc,address,size,user):
        if address in [0x428751,0x4288be]:boundaries.append(address);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,inspect)
    u.reg_write(UC_X86_REG_ESI,m);u.reg_write(UC_X86_REG_EBP,frame)
    u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x42867c,0x4288bf,count=100000)
    relative=False;disaster=False
    if not present or free_switch:expected=True
    elif protected and candidate!=1.:expected=False
    else:
        denominator=ext(1-ext(candidate*current))
        relative=denominator>0 and ext(ext(candidate-current)/denominator)>native.value(0x5d8654,'f')
        disaster=current<1. and ratio**(elapsed/10)<native.value(0x5d8658,'f') and candidate>0
        expected=relative or disaster
    assert boundaries==[0x428751 if expected else 0x4288be],(candidate,current,protected,ratio,elapsed,boundaries,expected)
    return dict(candidate=candidate,current=current,free_switch=free_switch,protected=protected,
                outcome_ratio=ratio,elapsed=elapsed,current_present=present,
                relative_improvement=relative,disaster_override=disaster,accepted=expected,native_outcome_world=world)

def verify():
    cases=[fixture(*v) for v in itertools.product([-1.,-.5,0.,.5,.95,1.],
            [-1.,0.,.5,.95,1.],[False,True],[False,True],[.00001,.1,1.],[1,5,10])]
    cases.extend(fixture(c,1.,False,True,1.,5,False) for c in [-1.,0.,1.])
    for baseline,gains,losses,missing,candidate,current,elapsed in itertools.product(
            [0.,.1],[0,3],[0,100],[False,True],[0.,.5,1.],[.5,1.],[1,5,10]):
        cases.append(fixture(candidate,current,False,False,1.,elapsed,world=(baseline,1000,0,gains,losses,missing)))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='1083 gate cases with explicit40a3b0 outcome double plus288 integration cases with real40a3b0/466870; real59bcc0 power throughout. Exact flag15/1a behavior,relative improvement and elapsed disaster override. No offset or selection commit in this gate; flag producers/full scheduler pending.')
    (ROOT/'modernization/docs/ai-switch-gate-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
