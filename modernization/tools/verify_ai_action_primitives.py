"""Native default action and utility primitives, including ABI and edge cases."""
import struct,json
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_model_native import ROOT,SHA

def call(u,entry,this,args,fp=False):
    sp=0x23f0000;stop=0x2000000;out=stop+32
    if fp:u.mem_write(stop,b'\xdd\x1d'+struct.pack('<I',out)+b'\x90')
    put(u,sp,'I'*(1+len(args)),stop,*args)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,this)
    u.emu_start(entry,stop+6 if fp else stop,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==(stop+6 if fp else stop)
    return struct.unpack('<d',u.mem_read(out,8))[0] if fp else u.reg_read(UC_X86_REG_EAX)

def verify():
    cases=[];a=0x2010000;group=a+0x400;out=group+128
    for blocked in [0,1,0xffffffff]:
        u=machine();put(u,group+0x39,'I',blocked)
        call(u,0x415640,a,[group,0,0])
        eligible=bytes(u.mem_read(a+0x149,1))[0];assert eligible==(blocked==0)
        for repeat in range(2):
            put(u,out,'f',12.5);result=call(u,0x415670,a,[out,0,0])&255
            assert result==int(blocked==0 and repeat==0)
            value=struct.unpack('<f',u.mem_read(out,4))[0]
            assert value==(-1.0 if result else 12.5)
        assert call(u,0x4156a0,a,[])==8
        assert call(u,0x419900,a,[group,0,0])&255==1
        cases.append(dict(kind='default_action',group_block=blocked,score=-1,execute_returns=1,prepare_delay=8))
    for action,weights in [(6,[0.3,0.4,0.3]),(11,[0.6,0.4,0.0]),(12,[0.4,0.6,0.0]),(8,[0.2,0.3,0.5])]:
        for probs in [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.],[0.2,0.3,0.5]]:
            u=machine();put(u,a+4,'I',action);put(u,out,'3f',*probs)
            put(u,0x6c48fc+12*action,'3f',*weights)
            result=call(u,0x414ff0,a,[out],True)
            assert abs(result-(weights[2]*probs[2]-weights[0]*probs[0]))<1e-6
            cases.append(dict(kind='utility',id=action,p=probs,score=result))
    u=machine();put(u,a+4,'I',6);put(u,out,'3f',0.,0.,1.);put(u,0x6c4944,'3f',0.,0.,3.)
    result=call(u,0x414ff0,a,[out],True)
    assert abs(result-.999)<1e-6
    cases.append(dict(kind='utility_upper_cap',score=result))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Real native default ID0 initialize/evaluate/delay/execute and tactical414ff0 utility; no imports or game launched')
    (ROOT/'modernization/docs/ai-action-primitives-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
