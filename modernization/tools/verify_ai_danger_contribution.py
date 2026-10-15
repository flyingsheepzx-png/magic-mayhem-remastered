"""Native529e40 contribution and52a0f0/52a3a0 consumers; reachability double."""
import itertools,json,math,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(kind,relation,reachable,x,energy,extra,state,defense,missing=False):
    u=machine();unit=0x2010000;wizard=unit+0xe4b;definition=0x2020000;cells=0x2030000
    put(u,0x6c5494,'II',4096,4096)
    put(u,0x6def58,'I',unit);put(u,0x6def5c,'I',2)
    put(u,0x643a80+0x154,'I',int(not missing));put(u,0x643a80+0x154+0xc,'I',1)
    put(u,0x643a80+0x154+0x18,'B',relation)
    put(u,0x643a80,'I',int(not missing));put(u,0x643a80+0xc,'I',1)
    put(u,0x643a80+0x18,'B',relation)
    put(u,unit+0xac,'I',definition);put(u,definition,'I',kind)
    put(u,definition+8,'II',1,1);put(u,definition+0x34,'I',int(defense))
    put(u,unit+0x174,'I',0);put(u,unit+0x7c,'I',state)
    put(u,unit+0xa8,'I',0);put(u,unit+0xe8,'I',energy);put(u,unit+0x91e,'I',extra)
    put(u,wizard+0xde7,'i',1)
    put(u,0x6eaf08,'I',cells);put(u,0x6eaf0c,'I',2)
    put(u,cells+4,'3i',0,0,0);put(u,cells+0x294+4,'3i',x,0,0)
    u.mem_write(0x542810,b'\xc2\x10\x00');checks=[]
    def hook(uc,address,size,user):
        if address!=0x542810:return
        s=uc.reg_read(UC_X86_REG_ESP);args=struct.unpack('<4I',uc.mem_read(s+4,16))
        assert args[:2]==(0,1) and uc.reg_read(UC_X86_REG_ECX)==0x6eaf08
        checks.append(list(struct.unpack('<5I',uc.mem_read(args[2],20))))
        uc.reg_write(UC_X86_REG_EAX,int(reachable))
    u.hook_add(UC_HOOK_CODE,hook)
    try:value=call(u,0x529e40,unit,[0,1])
    except AssertionError:
        raise AssertionError((kind,relation,reachable,x,energy,extra,state,defense,hex(u.reg_read(UC_X86_REG_EIP))))
    admitted=bool(relation and not missing and reachable)
    # Exact representable inputs used; avoid ambiguous rounding thresholds.
    numerator=((energy&0xffffff00)+extra)*20
    expected=math.trunc(numerator/(math.sqrt(x*x)*native.value(0x5c72a8,'d')+native.value(0x5c72a0,'d'))) if admitted else 0
    if state:expected=math.trunc(expected/2)
    expected=(expected*10)&0xffffffff
    assert value==expected,(kind,relation,reachable,x,energy,extra,state,value,expected)
    assert len(checks)==int(bool(relation and not missing))
    put(u,unit+0x922,'I',99);put(u,unit+0x92a,'I',50)
    stop=0x2001000;out=stop+32;sp=0x23f0000
    u.mem_write(stop,b'\xdd\x1d'+struct.pack('<I',out)+b'\x90')
    put(u,sp,'II',stop,0);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,unit)
    u.emu_start(0x52a0f0,stop+6,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop+6
    ratio=struct.unpack('<d',u.mem_read(out,8))[0]
    expected_ratio=native.value(0x5c5bb0,'f') if missing else (value-50)/100
    assert ratio==expected_ratio,(ratio,expected_ratio)
    assert len(checks)==2*int(bool(relation and not missing))
    return dict(kind=kind,relation=relation,reachable=reachable,x=x,energy=energy,extra=extra,state=state,defense=defense,missing_wizard=missing,value=value,reachability_calls=len(checks),relative_contribution=ratio)

def consumers():
    cases=[]
    for kind,status,hp,maxhp,danger,safety in itertools.product((0,24,25,26,1),(0,1),(49,50,51),(100,101),(0,1,2,100),(0,1,99)):
        u=machine();unit=0x2010000;definition=0x2020000
        put(u,unit+0xac,'I',definition);put(u,definition,'I',kind);put(u,definition+0x18,'I',maxhp)
        put(u,unit+0x174,'i',-1);put(u,unit+0x7c,'I',status);put(u,unit+0xe4,'I',hp)
        put(u,unit+0x922,'ii',danger,safety)
        result=call(u,0x52a3a0,unit,[])
        expected=int(kind in (0,24,25,26) and status==0 and hp<=maxhp//2 and danger/(safety+1)>native.value(0x5c5a88,'d'))
        assert result==expected
        cases.append(dict(kind=kind,status=status,hp=hp,maxhp=maxhp,danger=danger,safety=safety,result=result))
    return cases

def verify():
    cases=[fixture(*v) for v in itertools.product((0,1),(0,1),(False,True),(0,100),(256,513),(0,10),(0,1),(False,True))]
    cases.append(fixture(0,1,True,0,256,0,0,False,True))
    gates=consumers()
    report=dict(result='passed',engine_sha256=SHA,contributions=cases,low_health_gates=gates,
        constants={hex(p):native.value(p,'d') for p in (0x5c72a8,0x5c72a0,0x5c5a88)},
        scope='257 whole529e40 cases and257 whole52a0f0 integrations with real466870/40e250/fixed point constructors/40a6b0/59bee0 and synthetic cell coordinates; only542810 reachability explicit double. Wizard/nonwizard movement descriptor paths,relation zero/missing wizard/failed reachability,energy truncation,extra and status halving covered. 720 whole52a3a0 cases use real5075f0 fallback max-health path,no doubles. Full danger producer accumulation,reachability algorithm,other unit states,negative/overflow/singular and missing/self consumer domains pending.')
    (ROOT/'modernization/docs/ai-danger-contribution-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',contributions=len(cases),low_health_gates=len(gates)))

if __name__=='__main__':verify()
