"""Nonfatal health event through real damage helper and relation counter."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word
from verify_ai_outcome_events import definition

def fixture(src,dst,named,amount,old,status,frozen,health=50):
    u=machine();unit=0x2010000;definition(u,unit,1)
    put(u,unit+0x174,'I',dst);put(u,unit+0xe4,'I',health)
    put(u,unit+0x7c,'I',status);put(u,unit+0x660,'I',1)
    put(u,0x6e9858,'B',frozen);put(u,0x689920,'I',0);put(u,0x5fbf28,'I',BASE)
    u.mem_write(BASE,b'\xa5'*SIZE)
    for i in range(8):u.mem_write(BASE+i*0x154+0x50,('Cornelius' if i==named else f'P{i}').encode()+b'\0')
    if src!=-1:
        put(u,BASE+src*0x154+0x18+dst,'B',1);put(u,BASE+src*0x154+0x28+dst,'B',0)
        put(u,BASE+src*0x154+0x30+dst*4,'I',old)
    expected=bytearray(u.mem_read(BASE,SIZE));enabled=health!=0 and not frozen
    invokes=enabled and src!=-1 and not status
    admitted=invokes and src!=dst and (src==named or dst==named)
    if admitted:
        word(expected,src*0x154+0x30+dst*4,old+amount)
        if old+amount>=100:
            expected[src*0x154+0x18+dst]=0;expected[dst*0x154+0x18+src]=0
    calls=[]
    def observe(uc,address,size,user):
        if address==0x4656c0:
            sp=uc.reg_read(UC_X86_REG_ESP);args=struct.unpack('<2I',uc.mem_read(sp+4,8))
            calls.append(dict(profile=uc.reg_read(UC_X86_REG_ECX),delta=args[0],target=args[1]))
        if address==0x507b82:uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,observe)
    sp=0x23f0000;stop=0x2000000
    put(u,sp,'5I',stop,(-amount)&0xffffffff,src&0xffffffff,0,0)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,unit)
    u.emu_start(0x5076f0,stop,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==(0x507b82 if enabled else stop)
    assert struct.unpack('<I',u.mem_read(unit+0xe4,4))[0]==(health-amount if enabled else health)
    assert calls==([dict(profile=BASE+src*0x154,delta=amount,target=dst)] if invokes else [])
    assert bytes(u.mem_read(BASE,SIZE))==expected
    return dict(source=src,victim=dst,named=named,amount=amount,old=old,status=status,frozen=frozen,health=health,counter_calls=calls,admitted=bool(admitted))

def verify():
    cases=[fixture(*v) for v in itertools.product((-1,0,3),(0,3),(-1,0,3),(1,10,49),(0,90,99),(0,1),(0,1))]
    cases.extend(fixture(src,0,0,10,99,0,0,health=0) for src in (-1,0,3))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='651 no-double5076f0 integrations. Enablednegative/nonfatalhealth branch entryto507b82 beforeUI suffix;dead/frozen trueearlyreturns. Real514990 nonfataldamage,416d80 value,4656c0 relationcounter execute. Type1/mode689920=0/noactionmemberships/damageattributionptr0/unit660=1;no world/UI/import calls. Independenthealth/profile/countercall checks. Damagepositiveabsoluteamount fed fromnegativehealthchange tosourceprofile againstvictimowner;ifsource!=-1/status7c=0. BothCorneliusdirections/self/missingowner/threshold covered. Fataldamage,otherunittypes/campaignstats/actionattribution/UI/world-save/network remainpending.')
    (ROOT/'modernization/docs/ai-damage-relation-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),counter_calls=sum(len(c['counter_calls']) for c in cases)))

if __name__=='__main__':verify()
