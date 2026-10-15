"""Native50a930 selector and50aa30 transition; callback effects explicit doubles."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESP
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import word

CALLBACKS={1:0x50acb0,2:0x510010,3:0x50afa0,4:0x50ccd0,5:0x50d580,6:0x50d840,7:0x50d860,8:0x50d850,9:0x50d870,10:0x50d8f0,11:0x51c510,12:0,13:0x51c230,14:0x521750,15:0x521770,16:0x521780}

def selector(state):
    u=machine();obj=0x2010000;u.mem_write(obj,b'\xa5'*0xe4b)
    before=bytes(u.mem_read(obj,0xe4b))
    result=call(u,0x50a930,obj,[state&0xffffffff])
    assert result==CALLBACKS.get(state,0) and u.reg_read(UC_X86_REG_EDX)==0
    assert bytes(u.mem_read(obj,0xe4b))==before
    return dict(state=state,callback=hex(result))

def transition(health,guard,previous,state):
    u=machine();obj=0x2010000;tree=0x2020000
    u.mem_write(obj,b'\xa5'*0xe4b);put(u,obj+0xe4,'I',health);put(u,obj+0x618,'I',guard)
    put(u,obj+0x5ec,'I',previous);put(u,obj+0x5f0,'I',42)
    put(u,obj+0x6e8,'I',0);put(u,obj+0x8f9,'I',tree);put(u,tree+8,'I',0)
    expected=bytearray(u.mem_read(obj,0xe4b));events=[]
    admitted=bool(health or state==16 or state==5 and previous!=5)
    callback=CALLBACKS[state]
    if admitted:
        if guard:word(expected,0x5f0,state)
        else:
            word(expected,0x5ec,state)
            if state not in (8,14):word(expected,0x5f0,0)
            word(expected,0x5f4,callback);word(expected,0x5f8,0)
    for address in set(CALLBACKS.values())-{0}:u.mem_write(address,b'\xc3')
    def observe(uc,address,size,user):
        if address in CALLBACKS.values():events.append((address,uc.reg_read(UC_X86_REG_ECX)))
    u.hook_add(UC_HOOK_CODE,observe)
    call(u,0x50aa30,obj,[state])
    assert bytes(u.mem_read(obj,0xe4b))==expected,(health,guard,previous,state)
    assert events==([(callback,obj)] if admitted and not guard else [])
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0008
    return dict(health=health,guard=guard,previous=previous,state=state,admitted=admitted,callbacks=events)

def verify():
    selectors=[selector(s) for s in (-1,0,*range(1,18),255,0x7fffffff)]
    cases=[transition(*v) for v in itertools.product((0,10),(0,1),(0,2,5,8,14),tuple(s for s in CALLBACKS if s!=12))]
    report=dict(result='passed',engine_sha256=SHA,selectors=selectors,transitions=cases,
        scope='21 whole50a930 no-double selectors and300 whole50aa30 transitions with onlyselectedcallbacks explicitno-op doubles. Actualselector maps1..16 except12null,EDX0;outsideindicesnull. Completeunit snapshots/stack/callbackaddress-this checked. Deadrejectsexcept16 or5whenprevious!=5;618guardqueuespending;unguardedupdatesstate/handler/offset0,clears pendingexcept8/14. Previous2 cleanup fixturesemptytree/effect0. Invalid/nullcallback invocation,nonempty effectcleanup andcallbackinternalbehavior/wholeownership/save-network pending.')
    (ROOT/'modernization/docs/ai-state-dispatch-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',selectors=len(selectors),transitions=len(cases)))

if __name__=='__main__':verify()
