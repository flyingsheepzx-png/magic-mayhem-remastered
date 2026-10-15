"""Whole50ab30 with real animation/reference helpers, guarded state transition."""
import itertools,json,struct
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import word

ZERO_WORDS=(0xb73,0x164,0xde3,0x963,0x932,0x6a0,0xb8b,0x684,0x6ac,0x698)
ZERO_BYTES=(0x71c,0x962,0x723,0x722)

def fixture(health,animation,pending,command,attached,special,refcount):
    u=machine();pool=0x2010000;stride=0xe4b;ref=pool+stride;u.mem_write(pool,b'\xa5'*(2*stride))
    put(u,0x6def58,'II',pool,2)
    put(u,pool+0xe4,'I',health);put(u,pool+0x618,'I',1)
    put(u,pool+0xa0,'I',animation);put(u,pool+0x5f0,'I',pending)
    put(u,pool+0x5fc,'I',command);put(u,pool+0x664,'I',attached)
    put(u,pool+0x64c,'I',1);put(u,pool+0x6a8,'I',1);put(u,pool+0x10c,'I',special)
    put(u,pool+8,'III',11,22,33);put(u,ref+0x668,'i',refcount)
    anim=0xbf3;put(u,pool+anim+0xfc,'I',4);put(u,pool+anim+0x84,'4I',99,1,4,2)
    expected=bytearray(u.mem_read(pool,2*stride))
    if animation:
        if animation in (1,2):
            index=2 if animation==1 else 1;base=anim+0x84;n=(4-index)*4
            expected[base+index*4:base+index*4+n]=expected[base+(index+1)*4:base+(index+1)*4+n]
            word(expected,anim+0xfc,3);word(expected,anim+0x108,2)
        word(expected,0xa0,0);word(expected,0x9c,0)
    if pending!=8:
        word(expected,0x784,0)
        if special==3:word(expected,0x108,0)
        for off in ZERO_WORDS:word(expected,off,0)
        for off in ZERO_BYTES:expected[off]=0
        if attached and command in (10,20):
            word(expected,0x664,0);word(expected,stride+0x668,max(0,refcount-1))
        word(expected,0xbc3,11);word(expected,0xbc7,22);word(expected,0xbcb,33)
        if health:word(expected,0x5f0,1)
    call(u,0x50ab30,pool,[])
    actual=bytes(u.mem_read(pool,2*stride))
    assert actual==expected,(health,animation,pending,command,attached,special,refcount,[(hex(i),actual[i],expected[i]) for i in range(2*stride) if actual[i]!=expected[i]][:10])
    return dict(health=health,animation=animation,pending=pending,command=command,attached=attached,special=special,refcount=refcount)

def verify():
    cases=[fixture(*v) for v in itertools.product((0,10),(0,1,2,3),(0,3,8),(0,10,20),(0,1),(0,3),(0,1,10))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='864 whole50ab30 no-double calls,actual54dce0/CRTmemmove/50eb60/50aa30. Unit618=1 nativeguard queuespending1 foralive;dead state requestignored. Animationa0=1/2 removescode4/1,othernonzero clearsa0/9c withoutremoval. Pending8 afteranimation skipsremainingcleanup. Command10/20 attachedreference decrement/clamp;specifiedmovement/flags/targetpositionreset andfulltwounit snapshot. C-locale/internalhelpers,validreference1. Unguardedstate/callbacks,otheranimationlists/overflow/invalidrefs/fullownership/save-network pending.')
    (ROOT/'modernization/docs/ai-command-cancel-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
