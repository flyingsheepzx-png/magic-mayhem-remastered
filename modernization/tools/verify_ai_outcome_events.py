"""Native healing and power-income attribution slices, with no function doubles."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_resource_value import run,signed
from verify_ai_model_native import ROOT,SHA

def memberships(u,unit,mode):
    actions=[0x2050000,0x2050400]
    for slot in range(2):
        g=0x2040000+slot*0x400
        put(u,unit+0x678+4*slot,'I',0 if mode=='absent' else g)
        put(u,g+0x39,'I',g+0x100)
        put(u,g+0x100+0x39,'I',g+0x200)
        put(u,g+0x200+5,'I',actions[0 if mode=='shared' else slot])
    return actions

def definition(u,unit,kind):
    d=0x2030000
    put(u,unit+0xac,'I',d);put(u,d,'I',kind);put(u,d+0x18,'I',100)
    put(u,unit+0xa8,'I',1);put(u,unit+0x174,'i',-1)
    gd=0x6a5f80+0x5c9
    put(u,gd,'I',kind);put(u,gd+0x18,'I',100);put(u,gd+0x58,'I',1)
    put(u,0x6a5f98,'I',100)
    for i in range(28):put(u,gd+0x1a0+4*i,'I',20);put(u,gd+0x280+4*i,'I',36)

def healing(kind,health,amount,credit,mode,frozen):
    u=machine();unit=0x2010000;definition(u,unit,kind)
    actions=memberships(u,unit,mode)
    put(u,unit+0xe4,'I',health);put(u,0x6e9858,'B',frozen)
    values=[];sp=0x23f0000;stop=0x2000000
    def inspect(uc,address,size,user):
        if address==0x507b51:values.append(signed(uc.reg_read(UC_X86_REG_EAX)))
        if address==0x507b82:uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,inspect)
    put(u,sp,'5I',stop,amount,0xffffffff,0,credit)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,unit)
    u.emu_start(0x5076f0,stop,count=100000)
    enabled=not frozen and health!=0
    after=min(100,health+amount) if enabled else health
    assert word(u,unit+0xe4)==after
    value=run(kind,after,after-health,0.,0.,0.)['value'] if enabled and credit else 0
    assert values==([value] if enabled and credit else [])
    for i,a in enumerate(actions):
        expected=0 if mode=='absent' or mode=='shared' and i else value*(2 if mode=='shared' else 1)
        assert signed(word(u,a+0x2f))==expected
        assert word(u,a+0x33)==0
    return dict(kind='healing',unit_type=kind,health=health,amount=amount,credit=credit,
                memberships=mode,frozen=frozen,health_after=after,value=value)

def power(mana,capacity,reserved,deadline,active,profile,mode):
    u=machine();powerunit=0x2010000;wizard=0x2020000
    definition(u,powerunit,1);actions=memberships(u,powerunit,mode)
    put(u,powerunit+0xfc,'I',active);put(u,powerunit+0x100,'I',deadline)
    put(u,powerunit+0x174,'I',2);put(u,0x6c4830,'I',100)
    put(u,0x5e1904,'I',20);put(u,0x5e1908,'I',3)
    row=0x643a80+2*0x154
    put(u,row,'I',1);put(u,row+12,'i',0 if profile else -1)
    put(u,0x6def58,'I',wizard);put(u,0x6def5c,'I',1)
    put(u,wizard+0xac,'I',0x2060000);put(u,0x2060000,'I',0)
    put(u,wizard+0x174,'I',2);put(u,0x644520,'I',3)
    put(u,wizard+0xe8,'I',mana);put(u,wizard+0xec,'I',capacity)
    put(u,wizard+0x17c,'II',19,reserved);put(u,wizard+0x190,'I',1)
    values=[]
    def inspect(uc,address,size,user):
        if address==0x50a0a4:values.append(signed(uc.reg_read(UC_X86_REG_EAX)))
    u.hook_add(UC_HOOK_CODE,inspect)
    u.reg_write(UC_X86_REG_ESI,powerunit);u.reg_write(UC_X86_REG_EBP,0)
    u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x509fa4,0x50a0da,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x50a0da
    due=active and deadline<100
    enabled=due and profile
    after=min(capacity*256,mana+3*256) if enabled else mana
    assert word(u,wizard+0xe8)==after
    assert word(u,powerunit+0x100)==(120 if due else deadline)
    effective=(after+reserved*256)//256
    delta=after//256-mana//256
    value=run(1,0,0,float(effective),float(delta),0.)['value'] if enabled else 0
    assert values==([value] if enabled else [])
    for i,a in enumerate(actions):
        expected=0 if mode=='absent' or mode=='shared' and i else value*(2 if mode=='shared' else 1)
        assert signed(word(u,a+0x2f))==expected
        assert word(u,a+0x33)==0
    return dict(kind='power_income',mana_fixed=mana,capacity=capacity,reserved=reserved,
                deadline=deadline,active=active,profile=profile,memberships=mode,
                mana_after=after,effective_mana=effective,integer_mana_gain=delta,value=value)

def acquisition(yield_amount,period,mode):
    u=machine();unit=0x2010000;definition(u,unit,1)
    actions=memberships(u,unit,mode)
    put(u,0x5e1908,'i',yield_amount);put(u,0x5e1904,'i',period)
    sp=0x23f0000;stop=0x2000000
    # Enter after51e7d0 registration; emulate the real caller's saved registers.
    put(u,sp,'4I',0,0,0,stop);u.reg_write(UC_X86_REG_ESP,sp)
    u.reg_write(UC_X86_REG_ESI,unit)
    u.emu_start(0x467c8c,stop,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop and u.reg_read(UC_X86_REG_EAX)==1
    event=struct.unpack('<f',struct.pack('<f',yield_amount/period))[0]
    value=run(1,0,0,0.,0.,event)['value']
    for i,a in enumerate(actions):
        expected=0 if mode=='absent' or mode=='shared' and i else value*(2 if mode=='shared' else 1)
        assert signed(word(u,a+0x2f))==expected and word(u,a+0x33)==0
    assert word(u,unit+0xfc)==0 and word(u,unit+0x100)==0
    return dict(kind='power_acquisition_reward',yield_amount=yield_amount,period=period,
                memberships=mode,event_float=event,value=value)

def verify():
    cases=[healing(*v) for v in itertools.product([0,1,26],[0,20,90,100],[0,5,20],
            [False,True],['absent','distinct','shared'],[False,True])]
    cases.extend(power(*v) for v in itertools.product([9*256+128,100*256],[10,100],
            [0,20],[99,100,101],[False,True],[False,True],['absent','distinct','shared']))
    cases.extend(acquisition(*v) for v in itertools.product([0,1,3,7],[1,20,30],['absent','distinct','shared']))
    report=dict(engine_sha256=SHA,result='passed',cases=cases,
                scope='No stubs. Healing5076f0 entry through507b82 before UI suffix, or true native early return for dead/frozen. Power509fa4..50a0da slice with real466870/507f00/416d80. Acquisition467c8c..467cd0 reward suffix with real522770/416d80, excludes51e7d0 world registration. Synthetic definitions, manager rows and ancestor groups. Full509e50, fatal damage and player UI suffix remain untested.')
    (ROOT/'modernization/docs/ai-outcome-event-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
