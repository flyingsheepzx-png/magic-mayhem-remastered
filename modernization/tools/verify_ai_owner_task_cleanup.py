"""Whole51edf0 with real5178c0 and reference releases; explicit callback doubles."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word

def fixture(command,match,attachment,active,health,friendly,state,pending):
    u=machine();pool=0x2010000;size=4;callback=0x2040000
    u.mem_write(pool,bytes(0xe4b*size));u.mem_write(BASE,bytes(SIZE))
    put(u,0x6def58,'II',pool,size);put(u,0x6df180,'I',size)
    put(u,BASE+0x18+1,'B',friendly);put(u,BASE+0x18+2,'B',friendly)
    # The command-dispatch guard618=1 makes native50db60(15) return early.
    # This fixture verifies release/selection logic, not dispatcher cancellation.
    for i in range(size):
        p=pool+i*0xe4b;put(u,p,'II',i,1 if i==0 else active)
        put(u,p+0xe4,'I',10 if i==0 or health else 0);put(u,p+0x174,'I',0 if i==0 else 1+i%2)
        put(u,p+0x668,'I',10);put(u,p+0x618,'I',1)
        if i:
            put(u,p+0x5fc,'I',command);put(u,p+0x64c,'I',0 if match else 1)
            put(u,p+0x6a8,'I',0 if match else 1);put(u,p+0x664,'I',attachment)
            put(u,p+0x164,'I',42);put(u,p+0x6a4,'I',42)
            put(u,p+0x5ec,'I',state);put(u,p+0x5f0,'I',pending)
            put(u,p+0x5f4,'II',callback,0x700)
    expected=bytearray(u.mem_read(pool,0xe4b*size));events=[];dispatch=[];wanted=[];wanted_dispatch=[]
    released=0
    for i in range(1,size):
        p=i*0xe4b
        if active and match:
            if attachment and command in (10,20):
                word(expected,p+0x664,0);released+=1;wanted_dispatch.append((pool+p,15))
            if command==8:word(expected,p+0x164,0);wanted_dispatch.append((pool+p,15))
    word(expected,0x668,10-released)
    for i in range(1,size):
        p=i*0xe4b
        if not (active and health and friendly and match):continue
        if command==20:
            word(expected,p+0x6a4,0);word(expected,p+0x6a8,-1);wanted.append(('callback',pool+p+0x700))
        if state in (3,9,10,11):wanted.append(('cancel',pool+p))
        if pending==3:word(expected,p+0x5f0,0)
    u.mem_write(callback,b'\xc3');u.mem_write(0x50ab30,b'\xc3')
    def observe(uc,address,size,user):
        if address==callback:events.append(('callback',uc.reg_read(UC_X86_REG_ECX)))
        if address==0x50ab30:events.append(('cancel',uc.reg_read(UC_X86_REG_ECX)))
        if address==0x50db60:
            sp=uc.reg_read(UC_X86_REG_ESP);dispatch.append((uc.reg_read(UC_X86_REG_ECX),struct.unpack('<I',uc.mem_read(sp+4,4))[0]))
    u.hook_add(UC_HOOK_CODE,observe)
    profile=bytes(u.mem_read(BASE,SIZE));call(u,0x51edf0,pool,[])
    assert bytes(u.mem_read(pool,len(expected)))==expected,(command,match,attachment,active,health,friendly,state,pending)
    assert bytes(u.mem_read(BASE,SIZE))==profile
    assert dispatch==wanted_dispatch and events==wanted,(dispatch,wanted_dispatch,events,wanted)
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0004
    return dict(command=command,match=match,attachment=attachment,active=active,health=health,friendly=friendly,state=state,pending=pending,released=released,events=events,dispatch=dispatch)

def verify():
    cases=[fixture(*v) for v in itertools.product((0,8,10,20),(0,1),(0,1),(0,1),(0,1),(0,1),(0,3,9,10,11),(0,3))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='1280 whole51edf0 calls with actual5178c0/4970b0/50eb60 andnative50db60 early618guard;50ab30 andtaskcallback explicitno-op event doubles. Fourunitpool,command0/8/10/20,match/attachment/activity/health/friend/state/pendingmatrix. Fullpool/profile/callbackorder/dispatchargs/referencecount/stackchecked. Firstrelease scan ignoreshealth/friend;secondactive/live/friendly scan clears20target/callback,invokesstate3/9/10/11 cancel,clearsmatchingpending3. Fullungated50db60/50ab30/callback sideeffects/owncommands/otherindices/groups/ownership/save-network pending.')
    (ROOT/'modernization/docs/ai-owner-task-cleanup-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
