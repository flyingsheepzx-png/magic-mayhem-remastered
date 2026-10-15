"""Verify native40ea00 signed feature normalization and weighted score fusion."""
import math,struct,json
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA

def recovered(selector,x,threshold,scale,weight,total,current):
    t=math.trunc(threshold);s=math.trunc(scale)
    v=(x-t)/(s+abs(x-t))
    if selector<0:v=-v
    v=struct.unpack('<f',struct.pack('<f',v))[0]
    def term(r,q):
        a=(1+q)**r;b=(1-q)**r
        a=struct.unpack('<f',struct.pack('<f',a))[0]
        return (a-b)/(a+b)
    old=0.0 if total==0 else term(total/(weight+total),current)
    old=struct.unpack('<f',struct.pack('<f',old))[0]
    new=term(weight/(weight+total),v)
    denominator=1+old*new
    return (old+new)/denominator if denominator>0 else 0.0,total+weight

def native(selector,x,t,s,w,total,score):
    u=machine();a=0x2010000;sp=0x23f0000;stop=0x2000000
    put(u,a,'2f',total,score)
    put(u,0x5f8260+abs(selector)*4,'f',t);put(u,0x5f87f0+abs(selector)*4,'f',s)
    put(u,sp,'IfII',stop,w,a,a+4)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,selector);u.reg_write(UC_X86_REG_EDX,x&0xffffffff)
    u.emu_start(0x40ea00,stop,count=200000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    weight,score=struct.unpack('<2f',u.mem_read(a,8))
    return score,weight

def verify():
    cases=[]
    for selector in [2,-2,60,-60,123,-123]:
        for x in [-100,0,20,100]:
            for w,total,current in [(1.,0.,0.),(2.,1.,0.3),(1.,5.,-0.5)]:
                args=(selector,x,20.9,30.8,w,total,current)
                expected=recovered(*args);actual=native(*args)
                assert max(abs(a-b) for a,b in zip(expected,actual))<2e-6,(args,expected,actual)
                cases.append(dict(selector=selector,x=x,weight=w,previous_weight=total,previous_score=current,score=actual[0],error=abs(expected[0]-actual[0])))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Real native40ea00 and59bcc0 power/59bee0 integer truncation; signed selectors, threshold/scale truncation and weighted nonlinear fusion; no game launched')
    (ROOT/'modernization/docs/ai-feature-utility-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),max_error=max(c['error'] for c in cases)))

if __name__=='__main__':verify()
