"""Native command handler selector and state15/16 forwarding integrations."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EAX
from verify_ai_training_math import machine,put,native
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import word

HANDLERS={1:0x50f090,2:0x5104b0,3:0x50f360,4:0,5:0,6:0x50f090,7:0,8:0x50e6f0,9:0x50e670,10:0x50e7a0,11:0,12:0,13:0x50f3b0,14:0x50f590,15:0x50f7c0,16:0x50f090,17:0x50f090,18:0x50eba0,19:0x50f090,20:0x5170e0,21:0x521790,22:0x50f090,23:0x5217e0,24:0x521dd0,25:0x50f090}

def selector(command):
    u=machine();obj=0x2010000;u.mem_write(obj,b'\xa5'*0xe4b);before=bytes(u.mem_read(obj,0xe4b))
    result=call(u,0x50da50,obj,[command&0xffffffff])
    assert result==HANDLERS.get(command,0) and u.reg_read(UC_X86_REG_EDX)==0
    assert bytes(u.mem_read(obj,0xe4b))==before
    return dict(command=command,handler=hex(result))

def forward(state,guard,oldcommand,probe,effect):
    u=machine();unit=0x2010000;u.mem_write(unit,b'\xa5'*0xe4b)
    put(u,unit+0x618,'I',guard);put(u,unit+0x5fc,'I',oldcommand);put(u,unit+0x7cd,'I',effect)
    expected=bytearray(u.mem_read(unit,0xe4b));events=[];command=23 if state==15 else 24
    if not guard:
        if oldcommand==2:
            word(expected,0x16c,1);word(expected,0x170,struct.unpack('<I',u.mem_read(unit+0xb63,4))[0])
        elif oldcommand!=15:word(expected,0x16c,0)
        word(expected,0x5fc,command)
        for off in (0xb77,0xb7b,0xb7f):word(expected,off,0)
        word(expected,0x600,HANDLERS[command]);word(expected,0x604,0)
    for a,n in ((0x510480,0),(0x50e3d0,8),(0x513f50,0)):
        u.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3')
    def observe(uc,address,size,user):
        if address not in (0x510480,0x50e3d0,0x513f50):return
        assert uc.reg_read(UC_X86_REG_ECX)==unit
        if address==0x510480:events.append(('probe',));uc.reg_write(UC_X86_REG_EAX,probe)
        elif address==0x50e3d0:
            sp=uc.reg_read(UC_X86_REG_ESP);args=struct.unpack('<2I',uc.mem_read(sp+4,8));assert args==(0x120,0)
            events.append(('animation',*args))
        else:events.append(('attached_effect',))
    u.hook_add(UC_HOOK_CODE,observe)
    call(u,0x521770 if state==15 else 0x521780,unit,[])
    wanted=[]
    if not guard:
        if state==16:wanted.append(('probe',))
        if state==15 or not probe:wanted.append(('animation',0x120,0))
        if effect==1:wanted.append(('attached_effect',))
    assert bytes(u.mem_read(unit,0xe4b))==expected and events==wanted
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0004
    return dict(state=state,command=command,guard=guard,oldcommand=oldcommand,probe=probe,effect=effect,events=events)

def verify():
    selectors=[selector(c) for c in (-1,0,*range(1,27),255)]
    forwards=[forward(*v) for v in itertools.product((15,16),(0,1),(0,2,15),(0,1),(0,1,2))]
    report=dict(result='passed',engine_sha256=SHA,selectors=selectors,forwarding_cases=forwards,
        scope='29 whole50da50 no-double selectors,72 whole521770/521780 integrations withreal50db60/50da50 andonly510480 probe,50e3d0 animation,513f50 attachedeffect doubles. Fullunit/ret/handler/callargs-order checked. State15→command23,16→24;618guardno-op;old2sets16c/170,old15preserves16c;newcommand/flags/handler installed. Command24probe skipsanimation ifnonzero;23alwaysanimation120,0;effect1 invokes513f50. Callback/commandnames,probe/animation/effectbody/fullcommanddispatcher/save-network pending.')
    (ROOT/'modernization/docs/ai-command-handlers-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',selectors=len(selectors),forwarding=len(forwards)))

if __name__=='__main__':verify()
