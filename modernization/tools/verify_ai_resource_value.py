"""Reconstruct416d80 health/mana/event valuation with actual native helpers."""
import itertools,json,struct,math
from fractions import Fraction
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_model_native import ROOT,SHA

def signed(x):return x-0x100000000 if x&0x80000000 else x

def ext(x):
    x=Fraction(x)
    if not x:return x
    sign=1 if x>0 else -1;x=abs(x)
    exponent=x.numerator.bit_length()-x.denominator.bit_length()
    power=lambda e:Fraction(2**e) if e>=0 else Fraction(1,2**(-e))
    if x<power(exponent):exponent-=1
    step=power(exponent-63);scaled=x/step;q,r=divmod(scaled.numerator,scaled.denominator)
    if 2*r>scaled.denominator or (2*r==scaled.denominator and q&1):q+=1
    return sign*q*step

def reciprocal(x):return ext(1/Fraction(x))

def run(kind,health,health_delta,mana,mana_delta,event):
    u=machine();type_id=1
    definition=0x6a5f80+type_id*0x5c9
    put(u,definition,'I',kind);put(u,definition+0x18,'I',100);put(u,definition+0x58,'I',1)
    put(u,0x6a5f98,'I',100)
    for opponent in range(28):
        put(u,definition+0x1a0+opponent*4,'I',20)
        put(u,definition+0x280+opponent*4,'I',36)
    sp=0x23f0000;stop=0x2000000
    put(u,sp,'Ii3f',stop,health_delta,mana,mana_delta,event)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,type_id);u.reg_write(UC_X86_REG_EDX,health)
    u.emu_start(0x416d80,stop,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    result=signed(u.reg_read(UC_X86_REG_EAX))
    wizard=kind in [0,24,25,26]
    hp=int(ext(ext(ext(reciprocal(health-health_delta+1)-reciprocal(health+1))*101**2)+Fraction(native.value(0x5c53e8,'d')))) if wizard else ((56*40*health_delta+99)//100)&0xffffffff
    if not wizard:hp=signed(hp)
    # Native truncates between the health, mana and event stages.
    combined=int(ext(ext(ext(reciprocal(mana+30-mana_delta)-reciprocal(mana+30))*180000)+hp))
    expected=int(ext(combined+ext(Fraction(event)*1000000)))
    assert result==expected,(kind,health,health_delta,mana,mana_delta,event,result,expected)
    return dict(unit_type=kind,health=health,health_delta=health_delta,mana=mana,mana_delta=mana_delta,event=event,value=result)

def verify():
    cases=[]
    for kind,health,delta,mana,mana_delta,event in itertools.product([0,24,25,26,1],[50,100],[0,10],[0.,50.],[0.,5.],[0.,.25]):
        cases.append(run(kind,health,delta,mana,mana_delta,event))
    for health,delta,mana_delta,event in itertools.product([20,100],[-10,10],[-5.,5.],[-.25,0.]):cases.append(run(0,health,delta,50.,mana_delta,event))
    assert run(0,20,10,50.,0.,0.)['value']>run(0,100,10,50.,0.,0.)['value']
    assert run(0,100,0,0.,5.,0.)['value']>run(0,100,0,50.,5.,0.)['value']
    report=dict(engine_sha256=SHA,result='passed',cases=cases,scope='Actual416d80,505bf0,505c50 and59bee0; no stubs. Includes wizard negative health/mana/event changes; nonwizard fixtures use nonnegative health changes. x87 extended intermediates reconstructed. Names descriptive; not all training-counter producers.')
    (ROOT/'modernization/docs/ai-resource-value-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
