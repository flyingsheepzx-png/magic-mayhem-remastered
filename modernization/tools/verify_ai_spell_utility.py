"""Native40ec70 postprocessing with controlled delay/RNG dependencies."""
import json,struct
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_feature_utility import recovered
from verify_ai_model_native import ROOT,SHA

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]

def run(spell,mana,delay,cost,multiplier,adjustment,rng,weight,score):
    u=machine();a=0x2010000;total=a+0x1000;out=total+4
    put(u,a+0xe8,'I',mana*256)
    put(u,total,'2f',weight,score)
    put(u,0x6b1270+spell*0x2d1,'I',cost)
    put(u,0x6b13e5+spell*0x2d1,'f',adjustment)
    # Test doubles for only the two state-dependent dependencies.
    u.mem_write(0x51e530,b'\xb8'+struct.pack('<I',delay)+b'\xc2\x08\x00')
    u.mem_write(0x54e200,b'\xb8'+struct.pack('<I',rng)+b'\xc3')
    for selector,threshold,scale in [(125,50.,20.),(126,10.,10.),(127,20.,30.)]:
        put(u,0x5f8260+4*selector,'f',threshold);put(u,0x5f87f0+4*selector,'f',scale)
    sp=0x23f0000;stop=0x2000000
    put(u,sp,'6I',stop,a,spell,total,out,multiplier)
    u.reg_write(UC_X86_REG_ESP,sp)
    u.emu_start(0x40ec70,stop,count=500000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    total,actual=struct.unpack('<2f',u.mem_read(total,8))
    if delay>200:expected=-1.
    else:
        expected,weight=recovered(125,mana,50.,20.,f32(weight*.1),weight,score)
        expected=f32(expected);weight=f32(weight)
        expected,weight=recovered(-126,delay,10.,10.,weight,weight,expected)
        expected=f32(expected);weight=f32(weight)
        expected,weight=recovered(-127,cost*multiplier,20.,30.,f32(weight/6),weight,expected)
        expected=f32(expected)
        expected=f32(((adjustment+1)*expected+adjustment-1)/((adjustment-1)*expected+adjustment+1))
        expected=max(-1.,min(1.,f32(expected+((rng&0x7fffffff)%100-50)*.001)))
    assert abs(expected-actual)<2e-6,(spell,mana,delay,adjustment,expected,actual)
    return dict(spell=spell,mana=mana,delay=delay,cost=cost,multiplier=multiplier,adjustment=adjustment,rng=rng,score=actual,error=abs(expected-actual))

def verify():
    cases=[]
    for spell in [41,74,82]:
        for delay in [0,10,200,201]:
            for adjustment in [.5,1.,2.]:
                cases.append(run(spell,80,delay,15,2,adjustment,99,3.,.4))
    for rng in [0,50,99,0xffffffff]:cases.append(run(41,5,100,15,1,1.,rng,2.,-.2))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Actual40ec70 plus real40ea00/pow/truncation; delay51e530 and RNG54e200 explicitly stubbed in emulator, not game writes')
    (ROOT/'modernization/docs/ai-spell-utility-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
