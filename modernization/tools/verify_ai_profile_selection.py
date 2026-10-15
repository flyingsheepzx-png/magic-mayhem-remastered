"""Whole native profile selection/initializer; only sprintf boundary doubled."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA

BASE=0x643a80
SIZE=0xaa8
def word(buf,offset,value):struct.pack_into('<I',buf,offset,value&0xffffffff)

def selection(selected,active,eligible,flag):
    u=machine();u.mem_write(BASE,b'\xa5'*SIZE)
    for i in range(8):
        put(u,BASE+i*0x154,'III',(active>>i)&1,flag if eligible>>i&1 else 0,0x12340000+i)
    expected=bytearray(u.mem_read(BASE,SIZE));word(expected,0xaa0,-1)
    valid=0<=selected<8
    if valid:
        for i in range(8):
            if active>>i&1 and eligible>>i&1:
                word(expected,i*0x154+8,int(i==selected))
                if i==selected:word(expected,0xaa0,i)
    result=call(u,0x4667c0,BASE,[selected&0xffffffff])
    assert result==int(valid and active>>selected&1 and eligible>>selected&1)
    assert bytes(u.mem_read(BASE,SIZE))==expected
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0008
    return dict(selected=selected,active_mask=active,eligible_mask=eligible,flag=flag,result=result)

def initialize(count,selected,fill):
    u=machine();u.mem_write(BASE,bytes([fill])*SIZE)
    before=bytes(u.mem_read(BASE,SIZE));expected=bytearray(before)
    for i in range(8):
        p=i*0x154
        for off in (0,4,8):word(expected,p+off,0)
        for off in (12,16,20):word(expected,p+off,-1)
        expected[p+0x18:p+0x20]=b'\x01'*8
        expected[p+0x20:p+0x50]=bytes(48)
    word(expected,0xaa0,-1);word(expected,0xaa4,0)
    valid=1<=count<8 and 0<=selected<count
    names=[]
    u.mem_write(0x59c1fd,b'\xc3')
    def sprintf(uc,address,size,user):
        if address!=0x59c1fd:return
        sp=uc.reg_read(UC_X86_REG_ESP)
        out,fmt,label,index=struct.unpack('<4I',uc.mem_read(sp+4,16))
        assert fmt==0x5d98c4 and index==len(names)
        assert label==struct.unpack('<I',uc.mem_read(0x5c5c5c,4))[0]
        raw=f'FixturePlayer{index}'.encode()+b'\0';names.append(index)
        uc.mem_write(out,raw);uc.reg_write(UC_X86_REG_EAX,len(raw)-1)
    u.hook_add(UC_HOOK_CODE,sprintf)
    if valid:
        for i in range(count):
            p=i*0x154
            word(expected,p,1);word(expected,p+4,1);word(expected,p+8,int(i==selected))
            raw=f'FixturePlayer{i}'.encode()+b'\0';expected[p+0x50:p+0x50+len(raw)]=raw
            word(expected,p+0x150,i)
            for j in range(8):
                if i!=j:
                    expected[p+0x18+j]=0;expected[j*0x154+0x18+i]=0
        word(expected,0xaa0,selected)
    result=call(u,0x466420,BASE,[count&0xffffffff,selected&0xffffffff])&255
    assert result==valid and names==list(range(count) if valid else [])
    assert bytes(u.mem_read(BASE,SIZE))==expected,(count,selected,fill)
    assert struct.unpack('<I',u.mem_read(0x5fbf28,4))[0]==BASE
    assert u.reg_read(UC_X86_REG_ESP)==0x23f000c
    return dict(count=count,selected=selected,fill=fill,result=result,formatted_slots=names)

def campaign_initializer(mask,fill):
    u=machine();u.mem_write(BASE,bytes([fill])*SIZE)
    # Global campaign label slots: four strings at stride307; skipped labels
    # compare byte-for-byte against the global sentinel string.
    sentinel=b'Unused\0';u.mem_write(0x6ead98,sentinel)
    labels=[b'Local\0']+[f'Foreign{i}'.encode()+b'\0' if mask>>(i-1)&1 else sentinel for i in range(1,4)]
    for i,raw in enumerate(labels):u.mem_write(0x658f10+307*i,raw)
    expected=bytearray(u.mem_read(BASE,SIZE))
    for i in range(8):
        p=i*0x154
        for off in (0,4,8):word(expected,p+off,0)
        for off in (12,16,20):word(expected,p+off,-1)
        expected[p+0x18:p+0x20]=b'\x01'*8
        expected[p+0x20:p+0x50]=bytes(48)
    word(expected,0xaa0,0);word(expected,0xaa4,0)
    created=[0]+[i for i in range(1,4) if mask>>(i-1)&1]
    for i in created:
        p=i*0x154;word(expected,p,1);word(expected,p+4,int(i==0));word(expected,p+8,1)
        raw=labels[i];expected[p+0x50:p+0x50+len(raw)]=raw
        for j in range(8):
            if i!=j:expected[p+0x18+j]=0;expected[j*0x154+0x18+i]=0
    result=call(u,0x4665b0,BASE,[])&255
    assert result==1 and bytes(u.mem_read(BASE,SIZE))==expected,(mask,fill)
    assert struct.unpack('<I',u.mem_read(0x5fbf28,4))[0]==BASE
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0004
    return dict(label_mask=mask,fill=fill,created_slots=created)

def verify():
    selects=[selection(*v) for v in itertools.product((-1,0,1,3,7,8), (0,1,85,128,255),(0,1,170,128,255),(1,0xffffffff))]
    inits=[initialize(*v) for v in itertools.product((-1,0,1,2,7,8),(-1,0,1,6,7,8),(0,165,255))]
    campaign=[campaign_initializer(*v) for v in itertools.product(range(8),(0,165,255))]
    report=dict(result='passed',engine_sha256=SHA,selection_cases=selects,initialization_cases=inits,campaign_initialization_cases=campaign,
        scope='300 whole4667c0 no-double selection cases and108 whole466420 initializer cases with onlyCRT sprintf doubled. Complete aa8 snapshot,return,stack cleanup andglobalprofile pointer asserted. Eligibility ECX profiles0/4 nonzero;writes8 in fixed643a80 array. Tests use matchingglobalbase;nonalias callers not covered. Initializer resets all8 eveninvalidinputs;validcount1..7;created4=1,local8=1;offdiagonal18 cleared symmetrically forcreated slots,diagonal1;names copied/index150 set. Sprintf content/localization andother initializers/save/network/role meaning pending.')
    report['campaign_scope']='24 whole4665b0 no-double cases,synthetic global fourlabel strings/sentinel;real465440/466a80/4667c0. Local0 active/4=1/8=1;non-sentinel slots1..3 active/4=0/8=1. Symmetric18 cleared forcreated slots. Index150 preserved. Actual labelproducer,caller mode,localization andsave/network pending.'
    (ROOT/'modernization/docs/ai-profile-selection-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',selection=len(selects),initialization=len(inits),campaign=len(campaign)))

if __name__=='__main__':verify()
