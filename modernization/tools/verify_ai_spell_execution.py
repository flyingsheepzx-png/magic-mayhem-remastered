"""Eight native targeted-spell executors; explicit external world/queue doubles."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_cure_targets import setup
from verify_ai_action_primitives import call
from verify_ai_training_math import put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

FAMILY={21:(0x4466f0,41,None),39:(0x44f9d0,74,0x90),
        43:(0x450780,78,0x7cd),44:(0x44c560,79,0x78c),
        47:(0x4500c0,83,0x7cd),48:(0x450ee0,84,0x7cd),
        51:(0x45bb60,85,0x8c),52:(0x45d2b0,42,0x94)}

def fixture(action,health,effect,mana,already,blocked,wait_mode,delay=0,real_recovery=False,potion=25):
    entry,spell,field=FAMILY[action]
    u,a,t,c=setup(health)
    if field is not None:put(u,t+field,'i',effect)
    put(u,a+0x162,'B',already);put(u,c+0xe8,'I',mana*256)
    put(u,c+0xec,'I',100);put(u,c+0xac,'I',0x2060000)
    put(u,0x2060000,'I',0);put(u,c+0x174,'I',2)
    put(u,0x6df180,'I',0);put(u,0x5e1908,'I',3)
    put(u,0x6b1270+spell*721,'I',10)
    if wait_mode=='stub':u.mem_write(0x51e530,b'\xb8'+struct.pack('<I',delay)+b'\xc2\x08\0')
    if wait_mode=='native_reserved':
        put(u,c+0x17c,'II',19,10);put(u,c+0x190,'I',1)
    u.mem_write(0x40ad00,b'\xb8'+struct.pack('<I',blocked)+b'\xc2\x10\0')
    if not real_recovery:u.mem_write(0x51d570,b'\xc3')
    else:
        assert wait_mode=='native_reserved'
        put(u,c+0x18c,'I',1);put(u,c+0x178,'I',1)
        put(u,0x6e1f0c,'I',0);put(u,0x644520,'I',3)
        put(u,0x6b1254,'I',20);put(u,0x6b1250,'I',0x2070000)
        put(u,0x2070000+19*32,'I',potion)
        u.mem_write(0x564e90,b'\xc2\x18\0')
    u.mem_write(0x57c6e0,b'\xc3')
    # Lucifer's Farewell44 post-submit world changes are traced, not emulated.
    u.mem_write(0x51f5b0,b'\xc3');u.mem_write(0x50fef0,b'\xc2\x04\0')
    commands=[];recover=[];post=[];wait=[]
    def inspect(uc,address,size,user):
        if address==0x57c6e0:
            ptr=uc.reg_read(UC_X86_REG_ECX)
            commands.append(dict(spell=word(uc,ptr),caster=word(uc,ptr+0x1c),
                                 target=word(uc,ptr+0x20),multiplicity=word(uc,ptr+0x24)))
        elif address==0x51d570:recover.append(uc.reg_read(UC_X86_REG_ECX))
        elif address in [0x51f5b0,0x50fef0]:post.append(hex(address))
        elif address==0x51e530:
            sp=uc.reg_read(UC_X86_REG_ESP)
            wait.append([word(uc,sp+4),word(uc,sp+8)])
    u.hook_add(UC_HOOK_CODE,inspect)
    result=call(u,entry,a,[0,0,0])&255
    active=health!=0 and (health!=200 if action==21 else effect<=0 if action==39 else effect==0)
    ready=(delay==0 if wait_mode=='stub' else mana>=10 or wait_mode=='native_reserved')
    replenish=active and not already and ready and mana<10
    # Executor39 intentionally falls through recovery into revalidation/submission.
    cast=active and not already and ready and (mana>=10 or action==39) and not blocked
    assert result==active,(action,health,effect,result,active)
    assert bool(recover)==replenish and bool(commands)==cast,(action,mana,wait_mode,commands,recover)
    assert wait==([[spell,1]] if active and not already else [])
    assert bytes(u.mem_read(a+0x162,1))[0]==int(bool(already or cast))
    if commands:assert commands==[dict(spell=spell,caster=77,target=123,multiplicity=1)]
    assert post==(['0x51f5b0','0x50fef0'] if cast and action==44 else [])
    if real_recovery:
        assert word(u,c+0xe8)==min(100,mana+(potion if replenish else 0))*256
        assert word(u,c+0x18c)==int(not replenish)
        assert word(u,c+0x190)==int(not replenish)
    return dict(action_id=action,health=health,effect=effect,mana=mana,
                already_submitted=already,blocked=blocked,wait_mode=wait_mode,
                delay_override=delay if wait_mode=='stub' else None,
                active=result,submitted=bool(commands),recovery_requested=bool(recover),
                real_recovery=real_recovery,mana_after=word(u,c+0xe8)//256)

def verify():
    cases=[]
    for action in FAMILY:
        for values in itertools.product([0,50,200],[-1,0,1],[9,10,20],[False,True],[False,True]):
            for mode in ['native','native_reserved']:cases.append(fixture(action,*values,mode))
            for delay in [0,1]:cases.append(fixture(action,*values,'stub',delay))
    cases.extend(fixture(action,50,0,9,False,blocked,'native_reserved',
                         real_recovery=True,potion=potion)
                 for action,blocked,potion in itertools.product(FAMILY,[False,True],[0,1,25]))
    report=dict(engine_sha256=SHA,result='passed',cases=cases,
                action_ids=sorted(FAMILY),family={str(i):v for i,v in FAMILY.items()},
                scope='Full native eight executors:3456 branch cases with recovery double,48 integrations with real51d570/468b10/type19/507f00 and effect sink564e90. Native wait/reserves and separate explicit delay overrides. World40ad00,queue57c6e0 and Lucifer Farewell44 post-submit helpers doubled. Synthetic cost10 isolates thresholds, not configured costs. No actual spell effects, path/world acceptance or full evaluation claim.')
    (ROOT/'modernization/docs/ai-spell-execution-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',actions=len(FAMILY),cases=len(cases)))

if __name__=='__main__':verify()
