"""Native41d2be unit eligibility/cursor and41dba3 contribution commit slices."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def selection(start,own,live,hp,visibility,relation,cell):
    u=machine();manager=0x2010000;units=0x2030000;sp=0x23e0000;endpoint=[]
    put(u,0x643a80,'II',1,0);put(u,0x643a80+0xc,'I',0)
    put(u,0x643a80+0x154+0x28,'B',visibility);put(u,0x643a80+0x154+0x18,'B',relation)
    put(u,manager+0x12099,'I',0);put(u,manager+0x1209d,'I',start)
    put(u,manager+0x120a5,'I',units+start*0xe4b)
    for i in range(125):
        a=units+i*0xe4b
        put(u,a+4,'I',live);put(u,a+0xe4,'I',hp)
        put(u,a+0x174,'I',0 if own else 1);put(u,a+0xde7,'i',cell)
    before=bytes(u.mem_read(units,125*0xe4b))
    def hook(uc,address,size,user):
        if address in (0x41d505,0x41d3a2):endpoint.append(address);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,manager)
    u.emu_start(0x41d2be,0x2000000,count=100000)
    eligible=bool(start<125 and live and hp and (own or (visibility and relation)) and cell!=-1)
    expected=start if eligible else 125
    assert endpoint==[0x41d505 if eligible else 0x41d3a2]
    assert word(u,manager+0x1209d)==expected
    assert word(u,manager+0x120a5)==units+expected*0xe4b
    assert bytes(u.mem_read(units,125*0xe4b))==before
    return dict(start=start,own=own,live=live,hp=hp,visibility=visibility,relation=relation,cell=cell,selected=eligible,cursor=expected)

def commit(value,total,spent):
    u=machine();manager=0x2010000;unit=0x2030000;sp=0x23e0000;end=[];calls=[]
    put(u,sp+0x1c,'I',manager);put(u,sp+0x3c,'I',spent)
    put(u,manager+0x120a5,'I',unit);put(u,manager+0x12099,'I',3)
    put(u,manager+0x1209d,'I',20);put(u,manager+0x120a9,'I',total)
    put(u,unit+0xde7,'I',17);u.mem_write(0x529e40,b'\xc2\x08\x00')
    def hook(uc,address,size,user):
        if address in (0x41d2b8,0x41dc10):end.append(address);uc.emu_stop()
        if address==0x529e40:
            s=uc.reg_read(UC_X86_REG_ESP)
            assert tuple(struct.unpack('<2I',uc.mem_read(s+4,8)))==(17,3)
            assert uc.reg_read(UC_X86_REG_ECX)==unit
            calls.append(1);uc.reg_write(UC_X86_REG_EAX,value&0xffffffff)
    u.hook_add(UC_HOOK_CODE,hook);u.reg_write(UC_X86_REG_ESP,sp)
    u.emu_start(0x41dba3,0x2000000,count=100000)
    assert calls==[1] and end==[0x41d2b8 if spent+1<4 else 0x41dc10]
    assert word(u,unit+0x92a)==value&0xffffffff
    assert word(u,manager+0x120a9)==(total+value)&0xffffffff
    assert word(u,manager+0x120a5)==unit+0xe4b and word(u,manager+0x1209d)==21
    assert word(u,sp+0x3c)==spent+1
    return dict(value=value,total=total,spent=spent,total_after=word(u,manager+0x120a9),continue_units=spent+1<4)

def verify():
    selection_cases=[selection(*v) for v in itertools.product((0,1,124,125),(False,True),(0,1),(0,100),(0,1),(0,1),(-1,0))]
    commits=[commit(*v) for v in itertools.product((0,10,-1,0x7fffffff),(0,100,0xffffffff),(0,1,2,3))]
    report=dict(result='passed',engine_sha256=SHA,selection=selection_cases,commits=commits,
        scope='256 no-double41d2be..41d505/41d3a2 unit eligibility/cursor cases:active valid role0 player staged,125 synthetic unit slots,unit+4/e4,owner/self vs foreign profile28/18 gates,cell=-1 andcursor0/1/124/125. Skipped slots do not mutate units;fixed scan boundary125,stridee4b. 48 native41dba3 commit-suffix cases with529e40 explicit return-value double verify field92a,total120a9 wrapping,pointer/index advance and4 processed-unit budget. Full unit evaluation/map accumulation,profile/restart/owner=-1 and scheduler timing pending.')
    (ROOT/'modernization/docs/ai-danger-unit-cursor-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',selection=len(selection_cases),commits=len(commits)))

if __name__=='__main__':verify()
