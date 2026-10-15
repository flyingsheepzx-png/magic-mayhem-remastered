"""Native Cure target gates and command lifecycle with explicit world test doubles."""
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import group,word
from verify_ai_model_native import ROOT,SHA

def setup(health,maxhealth=200,poison=0,wizard=False,illusion=0,effect=0):
    u=machine();u.mem_map(0,0x1000)
    a=0x2010000;target=a+0x1000;caster=target+0x1000;definition=caster+0x1000;g=definition+0x1000
    put(u,a+0x149,'B',1);put(u,a+0x14a,'I',caster);put(u,a+0x152,'I',g)
    put(u,a+0x15e,'I',target);put(u,a+0x16,'I',100)
    put(u,target,'I',123);put(u,caster,'I',77)
    put(u,target+0xac,'I',definition);put(u,definition,'I',0 if wizard else 1)
    put(u,definition+0x18,'I',maxhealth);put(u,target+0x8c1,'I',maxhealth)
    put(u,target+0x174,'i',-1);put(u,target+0xe4,'I',health)
    put(u,target+0x8d5,'I',poison);put(u,target+0x7c,'I',illusion);put(u,target+0x78c,'I',effect)
    put(u,0x6b85ed,'I',100);put(u,0x6b85e9,'I',10)
    put(u,caster+0xe8,'I',20<<8)
    put(u,0x6c5494,'I',128);put(u,0x6c5498,'I',128);put(u,0x5d854c,'I',0)
    group(u,g,unit=target);put(u,a+0x156,'I',call(u,0x407920,g,[]))
    return u,a,target,caster

def gate(health,poison=0,illusion=0,effect=0,blocked=0,deadline=0):
    u,a,t,c=setup(health,poison=poison,illusion=illusion,effect=effect)
    u.mem_write(0x40ad00,b'\xb8'+struct.pack('<I',blocked)+b'\xc2\x10\0')
    hits=[]
    def inspect(uc,address,size,user):
        if address==0x4463be:
            hits.append(dict(target=word(uc,a+0x15a),heal_feature=uc.reg_read(UC_X86_REG_EDI)))
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,inspect,begin=0x4463be,end=0x4463be)
    sp=0x23f0000;stop=0x2000000
    put(u,sp,'4I',stop,0x2030000,0,deadline);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,a)
    u.emu_start(0x446210,stop,count=100000)
    # The noncritical route requires missing health >= the complete heal amount.
    eligible=illusion==0 and effect==0 and blocked==0 and deadline<=100 and (((health-poison//2)&0xffffffff)<100 or 200-health>=100)
    assert bool(hits)==eligible,(health,poison,illusion,effect,blocked,deadline,hits)
    if hits:assert hits[0]['heal_feature']==min(200-health,100)+poison
    return dict(kind='target_gate',health=health,poison_forecast=poison,illusion=illusion,existing_effect=effect,blocked=blocked,deadline=deadline,eligible=eligible,selected=hits)

def execution(health,delay=0,mana=20,already_cast=0,blocked=0):
    u,a,t,c=setup(health);put(u,a+0x162,'B',already_cast);put(u,c+0xe8,'I',mana<<8)
    u.mem_write(0x51e530,b'\xb8'+struct.pack('<I',delay)+b'\xc2\x08\0')
    u.mem_write(0x40ad00,b'\xb8'+struct.pack('<I',blocked)+b'\xc2\x10\0')
    u.mem_write(0x51d570,b'\xc3');u.mem_write(0x57c6e0,b'\xc3')
    commands=[];recover=[]
    def inspect(uc,address,size,user):
        if address==0x57c6e0:
            ptr=uc.reg_read(UC_X86_REG_ECX)
            commands.append(dict(spell=word(uc,ptr),caster=word(uc,ptr+0x1c),target=word(uc,ptr+0x20),multiplicity=word(uc,ptr+0x24)))
        elif address==0x51d570:recover.append(uc.reg_read(UC_X86_REG_ECX))
    u.hook_add(UC_HOOK_CODE,inspect)
    result=call(u,0x4466f0,a,[0,0,0])&255
    active=health not in (0,200)
    cast=active and not already_cast and delay==0 and mana>=10 and not blocked
    replenish=active and not already_cast and delay==0 and mana<10
    assert result==active
    assert bool(commands)==cast and bool(recover)==replenish
    if commands:assert commands==[dict(spell=41,caster=77,target=123,multiplicity=1)]
    assert bytes(u.mem_read(a+0x162,1))[0]==int(bool(already_cast or cast))
    return dict(kind='execution',health=health,delay=delay,mana=mana,already_cast=already_cast,blocked=blocked,active=result,commands=commands,replenish=bool(recover))

def verify():
    cases=[gate(h,p) for h in [0,49,99,100,101,150,199,200] for p in [0,40]]
    cases.extend([gate(49,illusion=1),gate(49,effect=1),gate(49,blocked=1),gate(49,deadline=101)])
    cases.extend(execution(h) for h in [0,49,199,200])
    cases.extend([execution(49,delay=1),execution(49,mana=9),execution(49,mana=10),execution(49,already_cast=1),execution(49,blocked=1)])
    for kind in [0,24,25,26]:
        u,a,t,c=setup(49,wizard=True)
        put(u,word(u,t+0xac),'I',kind)
        u.mem_write(0x40ad00,b'\x31\xc0\xc2\x10\0')
        reached=[]
        def priority(uc,address,size,user):
            reached.append(struct.unpack('<f',uc.mem_read(0x2030000,4))[0]);uc.emu_stop()
        u.hook_add(UC_HOOK_CODE,priority,begin=0x4465a5,end=0x4465a5)
        sp=0x23f0000;stop=0x2000000
        put(u,sp,'4I',stop,0x2030000,0,0);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,a)
        u.emu_start(0x446210,stop,count=100000)
        assert reached==[1.0]
        cases.append(dict(kind='critical_wizard_priority',unit_type=kind,score_before_health_and_mana_postprocess=1.0))
    report=dict(engine_sha256=SHA,result='passed',cases=cases,scope='Real446210 target gates up to candidate acceptance,4079f0 recursion,5075f0 maxhealth,4466f0 full lifecycle and coordinate constructors. World/path validation40ad00,delay51e530,mana recovery51d570,command submission57c6e0 explicitly stubbed. Target-specific scoring and actual healing not tested.')
    (ROOT/'modernization/docs/ai-cure-target-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
