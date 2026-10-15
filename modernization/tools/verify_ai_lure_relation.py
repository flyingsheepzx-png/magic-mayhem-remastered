"""Effect50 dispatch prefix through actual4656c0, before graphics/world suffix."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word

def fixture(caster_owner,victim_owner,named,caster_index,health):
    u=machine();u.mem_map(0,4096);effect=0x2010000;pool=0x2020000;victim=pool+0xe4b
    put(u,0x6def58,'I',pool);put(u,0x6def5c,'I',2);put(u,0x5fbf28,'I',BASE)
    put(u,effect+0x44,'III',caster_index&0xffffffff,1,50)
    put(u,pool+0x174,'I',caster_owner);put(u,victim+0x174,'I',victim_owner)
    put(u,victim+0xe4,'I',health);put(u,0x6ba09b,'I',1234)
    u.mem_write(BASE,b'\xa5'*SIZE)
    for i in range(8):u.mem_write(BASE+i*0x154+0x50,('Cornelius' if i==named else f'P{i}').encode()+b'\0')
    put(u,BASE+victim_owner*0x154+0x18+caster_owner,'B',1)
    put(u,BASE+victim_owner*0x154+0x28+caster_owner,'B',0)
    put(u,BASE+victim_owner*0x154+0x30+caster_owner*4,'I',90)
    expected=bytearray(u.mem_read(BASE,SIZE));calls=[]
    invokes=health!=0 and caster_index==0
    if invokes and caster_owner!=victim_owner and named in (caster_owner,victim_owner):
        word(expected,victim_owner*0x154+0x30+caster_owner*4,190)
        expected[victim_owner*0x154+0x18+caster_owner]=0
        expected[caster_owner*0x154+0x18+victim_owner]=0
    def observe(uc,address,size,user):
        if address in (0x48d03a,0x48d122):uc.emu_stop()
        if address==0x4656c0:
            sp=uc.reg_read(UC_X86_REG_ESP)
            calls.append((uc.reg_read(UC_X86_REG_ECX),*struct.unpack('<2I',uc.mem_read(sp+4,8))))
    u.hook_add(UC_HOOK_CODE,observe)
    sp=0x23f0000;put(u,sp,'I',0x2000000);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,effect)
    u.emu_start(0x48b0f0,0x2000000,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==(0x48d122 if health else 0x48d03a)
    assert calls==([(BASE+victim_owner*0x154,100,caster_owner)] if invokes else [])
    assert bytes(u.mem_read(BASE,SIZE))==expected
    assert struct.unpack('<I',u.mem_read(effect+0x198,4))[0]==victim
    if health:
        assert struct.unpack('<2I',u.mem_read(victim+0x780,8))[0]==1234
        assert struct.unpack('<I',u.mem_read(victim+0x788,4))[0]==0xffffffff
    return dict(caster=caster_owner,victim=victim_owner,named=named,caster_index=caster_index,health=health,counter_calls=calls)

def verify():
    cases=[fixture(*v) for v in itertools.product(range(8),range(8),(-1,0,7),(-1,0,2),(0,10))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='1152 no-double48b0f0 entryprefix calls,actualspell50 jumptable/CRTitoa/4656c0;stops48d03a deadtarget or48d122 beforegraphics. All8x8owners,uniqueCorneliusnone/0/7,casterindexmissing/valid/outofrange,targethealth0/10. Victimprofile receivesdelta100 againstcasterowner;direction differs fromhealthdamagecounter. Target198 resolution/780duration/788-1 andfullprofiles checked. Syntheticduration1234;actualconfiglabelLure andID mapping static. Full effect/world/UI,otherindices/statuses/types/expiry/save/network pending.')
    (ROOT/'modernization/docs/ai-lure-relation-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),counter_calls=sum(len(c['counter_calls']) for c in cases)))

if __name__=='__main__':verify()
