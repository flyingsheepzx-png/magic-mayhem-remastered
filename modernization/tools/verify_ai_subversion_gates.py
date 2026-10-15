"""Native effect54 prefix, actual RNG/profile/counter, before world conversion."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word

def fixture(strength,resistance,checkmask,random_value,kind,capacity,phase=0,health=10,target_index=1):
    u=machine();u.mem_map(0,4096);effect=0x2010000;pool=0x2020000;victim=pool+0xe4b;wizard=pool+2*0xe4b;definition=0x2040000
    put(u,0x6def58,'I',pool);put(u,0x6def5c,'I',3);put(u,0x5fbf28,'I',BASE)
    put(u,effect+0x44,'III',0,target_index&0xffffffff,54);put(u,effect+0x28,'I',phase)
    put(u,pool+0x174,'I',0);put(u,victim+0x174,'I',1);put(u,victim+0xe4,'I',health)
    put(u,victim+0xac,'I',definition);put(u,definition,'I',kind);put(u,victim+0x84,'I',resistance)
    put(u,wizard+0x8f1,'II',10,9 if capacity=='free' else 10)
    row=54*721
    put(u,0x6b1274+row,'I',strength)
    put(u,0x6b13d5+row,'III',int(bool(checkmask&1)),int(bool(checkmask&2)),int(bool(checkmask&4)))
    put(u,0x6b13e9+row,'I',30);put(u,0x6e1f30,'I',0)
    rng=0x6e1ac8;put(u,rng,'4I',0,1,random_value,0)
    u.mem_write(BASE,b'\xa5'*SIZE)
    for i in range(8):u.mem_write(BASE+i*0x154+0x50,('Cornelius' if i==1 else f'P{i}').encode()+b'\0')
    put(u,BASE,'I',1);put(u,BASE+12,'i',-1 if capacity=='absent' else 2)
    put(u,BASE+0x154+0x18,'B',1);put(u,BASE+0x154+0x28,'B',0);put(u,BASE+0x154+0x30,'I',90)
    expected=bytearray(u.mem_read(BASE,SIZE));calls=[];rngcalls=[]
    eligible_target=target_index in (0,1,2) and target_index!=-1
    # Early fixtures intentionally use only index1, -1 oroutofrange3.
    assert target_index in (1,-1,3)
    if target_index==-1:stop=0x48cbb0;accepted=False;tested=False
    elif phase in (6,7,11,30):stop=0x48c3e5;accepted=False;tested=False
    elif not eligible_target or not health:stop=0x48cd47;accepted=False;tested=False
    else:
        tested=True;roll=(random_value&0x7fffffff)%100
        probability=(100*strength)//(strength+resistance) if checkmask else None
        accepted=(not checkmask or roll<probability) and kind not in (0,24,25,26) and capacity!='blocked'
        stop=0x48c083 if accepted else 0x48c285
        if accepted:
            word(expected,0x154+0x30,190);expected[0x154+0x18]=0;expected[0x18+1]=0
    def observe(uc,address,size,user):
        if address in (0x48cbb0,0x48c3e5,0x48cd47,0x48c083,0x48c285):uc.emu_stop()
        if address==0x54e200:rngcalls.append(uc.reg_read(UC_X86_REG_ECX))
        if address==0x4656c0:
            sp=uc.reg_read(UC_X86_REG_ESP);calls.append((uc.reg_read(UC_X86_REG_ECX),*struct.unpack('<2I',uc.mem_read(sp+4,8))))
    u.hook_add(UC_HOOK_CODE,observe)
    sp=0x23f0000;put(u,sp,'I',0x2000000);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,effect)
    u.emu_start(0x48b0f0,0x2000000,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    assert calls==([(BASE+0x154,100,0)] if accepted else [])
    assert bytes(u.mem_read(BASE,SIZE))==expected
    assert rngcalls==([rng] if tested and checkmask else [])
    if rngcalls:
        successors=struct.unpack_from('<2I',native.image,0x5eb940-0x400000)
        assert tuple(struct.unpack('<4I',u.mem_read(rng,16)))==(*successors,random_value,0)
    else:assert tuple(struct.unpack('<4I',u.mem_read(rng,16)))==(0,1,random_value,0)
    after=struct.unpack('<I',u.mem_read(victim+0x84,4))[0]
    assert after==(resistance-resistance*30//100 if tested and not accepted and kind not in (0,24,25,26) else resistance)
    return dict(strength=strength,resistance=resistance,checkmask=checkmask,random_value=random_value,kind=kind,capacity=capacity,phase=phase,health=health,target_index=target_index,accepted=accepted,stop=hex(stop),resistance_after=after)

def verify():
    pairs=[(s,r) for s,r in itertools.product((0,1,8,100),(0,8,100)) if s+r]
    cases=[fixture(s,r,*v) for s,r in pairs for v in itertools.product((0,1,2,4),(0,49,50,99,0xffffffff),(0,1,24,25,26),('free','blocked','absent'))]
    early=[fixture(8,8,1,0,1,'free',phase=phase,health=h,target_index=i) for phase,h,i in itertools.product((0,6,7,11,30),(0,10),(-1,1,3))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,early_cases=early,
        scope='3300 no-double48b0f0 effect54 entryprefix cases plus30 earlytarget/phase fixtures. ActualCRTitoa,466870 profilewizard,54e200 RNG and4656c0 execute. Stopsbeforeworld conversion48c083 orafterfailureMR48c285,early48cbb0/48c3e5/48cd47. Independentunsignedprobability/strictthreshold/type/capacity gates,fullprofile/counter/RNGstate/resistance checks. Syntheticstrength/MR/30percent;RNGindices0/1 state withcontrollednativeXOR output. Wizard types0/24/25/26neverconvert;wizard8f5>=8f1 blocks;no wizard permits. Anycheckflag enables floor100*S/(S+MR),roll&7fffffff mod100;failure ordinarytype MR-=floor30*MR/100. Fullworldownership/suffix,otherflags/invalidcasters/zero-denominator/overflow/save/network pending.')
    (ROOT/'modernization/docs/ai-subversion-gates-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),early=len(early),accepted=sum(c['accepted'] for c in cases)))

if __name__=='__main__':verify()
