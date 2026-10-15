"""Native retirement decision/label slices, separate from destructive cleanup."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_resource_value import ext
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]

def setup(baseline=.1,current=100,safety=999,gains=0,losses=0,missing=False):
    u=machine();a=0x2010000;g=a+0x400;m=g+0x400;unit=m+0x2000;node=unit+0x2000;table=node+128
    put(u,a,'I',table);put(u,a+8,'I',g);put(u,g+4,'B',1)
    put(u,a+0x23,'i',3);put(u,a+0x27,'i',2)
    put(u,a+0x2b,'f',baseline);put(u,a+0x2f,'ii',gains,losses)
    put(u,0x643a80+2*0x154,'I',int(not missing));put(u,0x643a80+2*0x154+12,'I',0)
    put(u,0x6def58,'I',unit);put(u,0x6def5c,'I',1)
    put(u,unit+0x922,'ii',current,safety)
    put(u,node+16,'I',a);put(u,table+24,'I',0x2000000);u.mem_write(0x2000000,b'\xc3')
    return u,a,g,m,unit,node

def label(baseline,current,safety,gains,losses,learning=True,slot=3,missing=False):
    u,a,g,m,unit,node=setup(baseline,current,safety,gains,losses,missing)
    put(u,g+4,'B',learning);put(u,a+0x23,'i',slot)
    u.reg_write(UC_X86_REG_ESI,a);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x428c54,0x428cfc,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x428cfc
    status=bytes(u.mem_read(0x6c3898+16+29*3,1))[0]
    actual=word(u,0x6c3898+16+29*3+0x19)
    if learning and slot>=0:
        eps=Fraction(native.value(0x5c5378,'d'))
        metric=Fraction(0) if missing else ext(Fraction(current,safety+1))
        ratio=f32(float(ext(ext(ext(Fraction(gains+1,losses+1))*ext(Fraction(f32(baseline))+eps))/ext(metric+eps))))
        expected=0 if ratio<=native.value(0x5c5348,'f') else 1 if ratio<=native.value(0x5c534c,'f') else 2
        assert status==2 and actual==expected,(ratio,status,actual,expected)
    else:assert status==0
    return dict(kind='label',baseline=baseline,current=current,safety=safety,gains=gains,losses=losses,learning=learning,slot=slot,missing=missing,status=status,label=actual if status else None)

from fractions import Fraction

def decision(score=.5,baseline=.1,current=100,safety=999,gains=0,losses=0,elapsed=5,duration=10,learning=True,ended=False,manager_flag=False,multiplayer=0):
    u,a,g,m,unit,node=setup(baseline,current,safety,gains,losses)
    put(u,g+4,'B',learning);put(u,a+0xc,'ii',100,100+duration);put(u,a+0x14,'B',ended);put(u,a+0x1b,'f',score)
    put(u,m+0x14,'I',100+elapsed);put(u,m+0x18,'B',manager_flag);put(u,0x6e1f0c,'I',multiplayer)
    seen=[]
    def capture(uc,address,size,user):seen.append(bool(uc.reg_read(UC_X86_REG_EBX)&255));uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,capture,begin=0x428c43,end=0x428c43)
    u.reg_write(UC_X86_REG_EAX,node);u.reg_write(UC_X86_REG_EBP,m);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x428b61,0x428c43+1,count=100000)
    ratio=(f32(baseline)+.001)*(gains+1)/(losses+1)/(current/(safety+1)+.001)
    early=learning and score<1 and ratio**(elapsed/duration)<native.value(0x5d8658,'f')
    expected=early or (manager_flag and multiplayer==0) or elapsed>=duration or ended
    assert seen==[expected],(seen,expected,ratio)
    return dict(kind='decision',score=score,baseline=baseline,current=current,safety=safety,gains=gains,losses=losses,elapsed=elapsed,duration=duration,learning=learning,ended=ended,manager_flag=manager_flag,multiplayer=multiplayer,retire=expected)

def verify():
    cases=[]
    for baseline,current,gains,losses in itertools.product([0.,.05,.1,.2],[0,100],[0,3],[0,3]):cases.append(label(baseline,current,999,gains,losses))
    cases.extend([label(.1,100,999,0,0,learning=False),label(.1,100,999,0,0,slot=-1),label(.1,100,999,0,0,missing=True)])
    for learning,ended,manager_flag,multiplayer,elapsed in itertools.product([False,True],[False,True],[False,True],[0,1],[5,10]):cases.append(decision(learning=learning,ended=ended,manager_flag=manager_flag,multiplayer=multiplayer,elapsed=elapsed))
    for score,baseline,elapsed in itertools.product([.5,1.],[0.,.1],[1,5,10]):cases.append(decision(score=score,baseline=baseline,current=1000,safety=0,elapsed=elapsed))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Actual428b61..428c43 decision and428c54..428cfc labels,466870 and477040. Synthetic manager/action/world. Retire callback at vtable+18 stubbed to no-op; native cleanup excluded.')
    (ROOT/'modernization/docs/ai-retirement-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
