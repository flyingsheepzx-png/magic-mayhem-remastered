"""Native availability and mana-wait prediction, including real unit enumeration."""
import json,struct,itertools
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import group,word
from verify_ai_model_native import ROOT,SHA
INF=0x7fffffff

def setup(cost=10,mana=0,capacity=100,kind=0,powers=1):
    u=machine();unit=0x2010000;definition=unit+0x2000;pool=definition+0x1000
    put(u,unit+0xac,'I',definition);put(u,definition,'I',kind)
    put(u,unit+0x174,'I',2);put(u,unit+0xe8,'I',mana);put(u,unit+0xec,'I',capacity)
    put(u,0x6b1270+41*721,'I',cost)
    put(u,0x5e1908,'I',3);put(u,0x5e1904,'I',20)
    put(u,0x6def58,'I',pool);put(u,0x6df180,'I',powers+3)
    for i in range(powers+3):
        p=pool+i*0xe4b
        put(u,p+4,'I',1);put(u,p+0xe4,'I',1);put(u,p+0xfc,'I',1);put(u,p+0x174,'I',2)
    put(u,pool+powers*0xe4b+0xfc,'I',0)
    put(u,pool+(powers+1)*0xe4b+0xe4,'I',0)
    put(u,pool+(powers+2)*0xe4b+0x174,'I',3)
    return u,unit

def verify():
    cases=[]
    for cost,mana,capacity,kind,powers,mult in itertools.product([0,10],[0,9*256+128,10*256],[9,100],[0,1,24],[0,2],[1,2]):
        u,unit=setup(cost,mana,capacity,kind,powers)
        actual=call(u,0x51e530,unit,[41,mult])
        deficit=cost*256*mult-mana
        expected=INF if cost>capacity else 0 if deficit<=0 else INF if kind not in [0,24,25,26] or not powers else ((deficit+3*256*powers-1)//(3*256*powers))*20
        assert actual==expected,(cost,mana,capacity,kind,powers,mult,actual,expected)
        cases.append(dict(kind='local_wait',cost=cost,mana_fixed=mana,capacity=capacity,unit_type=kind,powers=powers,multiplicity=mult,wait=actual))
    for effect_kind,active,amount in [(19,1,10),(19,0,10),(18,1,10),(19,1,9)]:
        u,unit=setup(powers=0)
        put(u,unit+0x17c,'II',effect_kind,amount);put(u,unit+0x17c+0x14,'I',active)
        actual=call(u,0x51e530,unit,[41,1]);expected=0 if effect_kind==19 and active and amount>=10 else INF
        assert actual==expected
        cases.append(dict(kind='reserved_mana_record',record_type=effect_kind,active=active,amount=amount,wait=actual))
    for cost,mana,capacity,powers in itertools.product([10],[0,10*256-1,10*256],[9,100],[0,2]):
        u,unit=setup(cost,mana,capacity,powers=powers)
        put(u,unit+0xe2b+4*3,'I',mana)
        put(u,0x6c5c84,'I',powers)
        for i in range(powers):put(u,0x6c5640+3*4+i*32,'I',2)
        actual=call(u,0x51e6c0,unit,[3,41])
        deficit=cost*256-mana
        expected=0 if deficit<=0 else INF if not powers or cost>capacity else ((deficit+3*256*powers-1)//(3*256*powers))*20
        assert actual==expected
        cases.append(dict(kind='other_owner_wait',mana_fixed=mana,capacity=capacity,powers=powers,wait=actual))
    # Full40a950 with real51e6c0/51e530. ECX=context group, EDX=caster group.
    for wizard,leaf,known in itertools.product([False,True],[False,True],[False,True]):
        u,unit=setup(mana=10*256,kind=0 if wizard else 1)
        caster=0x2020000;context=caster+0x400;targetgroup=context+0x400;targetunit=targetgroup+0x400;out=targetunit+0x1000
        put(u,targetunit+0x174,'I',3)
        group(u,caster,unit=unit if leaf else 0,children=[] if leaf else [targetgroup])
        group(u,targetgroup,unit=targetunit);group(u,context,children=[targetgroup])
        put(u,unit+0xe2b+3*4,'I',10*256);put(u,0x5d854c,'I',0)
        put(u,0x6b13ed+41*721+4*(2+3*8),'I',int(known))
        sp=0x23f0000;stop=0x2000000
        put(u,sp,'3I',stop,41,out);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,context);u.reg_write(UC_X86_REG_EDX,caster)
        u.emu_start(0x40a950,stop,count=100000)
        assert u.reg_read(UC_X86_REG_EIP)==stop
        available=u.reg_read(UC_X86_REG_EAX)&255;wait=word(u,out)
        assert available==int(wizard and leaf and known)
        assert wait==(0 if available else INF)
        cases.append(dict(kind='availability',wizard=wizard,leaf=leaf,known=known,available=available,wait=wait))
    for owner,delta,initial in itertools.product([2,3],[-10000,0,10000],[0,15*256]):
        u,unit=setup(mana=7*256,capacity=10)
        put(u,unit+0xe2b+owner*4,'I',initial)
        put(u,unit+0x17c,'II',19,5);put(u,unit+0x17c+0x14,'I',1)
        call(u,0x507fa0,unit,[owner,delta&0xffffffff])
        value=word(u,unit+0xe2b+owner*4)
        expected=12*256 if owner==2 else min(10*256,max(0,initial+delta))
        assert value==expected
        cases.append(dict(kind='projected_mana_update',owner=owner,delta=delta,initial=initial,value=value))
    for spell,count in itertools.product([0,24,25,26,41],[0,29,30]):
        u,unit=setup();put(u,unit+0x56c,'I',count)
        address=0x6b13ed+spell*721+2*36;put(u,address,'I',0)
        call(u,0x509b60,unit,[spell])
        allowed=spell not in [0,24,25,26] and count<30
        assert word(u,unit+0x56c)==count+allowed
        assert word(u,address)==int(allowed)
        if allowed:assert word(u,unit+0x570+4*count)==spell
        cases.append(dict(kind='innate_spell_registration',spell=spell,count=count,registered=allowed))
    for mask in [0,1,4,0x55,0xff]:
        u,unit=setup(mana=20*256);cmd=0x2030000;put(u,cmd,'I',41)
        for observer in range(8):
            put(u,unit+0x24+observer*4,'I',int(bool(mask&(1<<observer))))
            put(u,0x6b13ed+41*721+4*(2+observer*8),'I',0)
            put(u,unit+0xe2b+observer*4,'I',20*256)
        # Native observation loop only; UI notification suffix explicitly skipped.
        def skip_ui(uc,address,size,user):uc.reg_write(UC_X86_REG_EIP,0x57b8df)
        u.hook_add(UC_HOOK_CODE,skip_ui,begin=0x57b85e,end=0x57b85e)
        u.reg_write(UC_X86_REG_EBP,unit);u.reg_write(UC_X86_REG_EBX,cmd);u.reg_write(UC_X86_REG_ESI,0)
        u.reg_write(UC_X86_REG_ESP,0x23f0000)
        u.emu_start(0x57b800,0x57b8ec,count=100000)
        assert u.reg_read(UC_X86_REG_EIP)==0x57b8ec
        for observer in range(8):
            visible=bool(mask&(1<<observer))
            assert word(u,0x6b13ed+41*721+4*(2+observer*8))==visible
            assert word(u,unit+0xe2b+observer*4)==(20*256 if observer==2 or not visible else 10*256)
        cases.append(dict(kind='native_observation_loop_slice',visibility_mask=mask,ui_notification_suffix_skipped=True))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Actual40a950,51e6c0,51e530,412aa0,4079f0,507fa0,509b60 with no stubs and synthetic worlds; five57b800..57b8ec observation-loop slices skip only UI notification suffix57b85e..57b8df. Full spell execution and type19 lifecycle pending.')
    (ROOT/'modernization/docs/ai-spell-availability-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
