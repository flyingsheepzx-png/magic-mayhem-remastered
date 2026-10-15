"""Whole4661c0 global mode/count initializer; sprintf alone doubled."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word

def fixture(mode,count,selected,fill):
    u=machine();u.mem_write(BASE,bytes([fill])*SIZE)
    put(u,0x6e1f0c,'I',mode);put(u,0x656630,'II',count&0xffffffff,selected&0xffffffff)
    first=b'FirstFixture\0';second=b'SecondFixtureLong\0'
    u.mem_write(0x2030000,first);u.mem_write(0x2030100,second)
    put(u,0x5c5c54,'II',0x2030000,0x2030100)
    expected=bytearray(u.mem_read(BASE,SIZE))
    for i in range(8):
        p=i*0x154
        for off in (0,4,8):word(expected,p+off,0)
        for off in (12,16,20):word(expected,p+off,-1)
        expected[p+0x18:p+0x20]=b'\x01'*8
        expected[p+0x20:p+0x50]=bytes(48)
    word(expected,0xaa0,-1);word(expected,0xaa4,0)
    valid=mode==1 or (1<=count<8 and 0<=selected<count)
    created=range(2) if mode==1 else range(count if valid else 0)
    names=[]
    u.mem_write(0x59c1fd,b'\xc3')
    def sprintf(uc,address,size,user):
        if address!=0x59c1fd:return
        assert mode!=1
        sp=uc.reg_read(UC_X86_REG_ESP)
        out,fmt,label,index=struct.unpack('<4I',uc.mem_read(sp+4,16))
        assert fmt==0x5d98c4 and index==len(names)
        assert label==struct.unpack('<I',uc.mem_read(0x5c5c5c,4))[0]
        raw=f'GlobalPlayer{index}'.encode()+b'\0';names.append(index)
        uc.mem_write(out,raw);uc.reg_write(UC_X86_REG_EAX,len(raw)-1)
    u.hook_add(UC_HOOK_CODE,sprintf)
    for i in created:
        p=i*0x154;word(expected,p,1)
        # Unlike466420, this path leaves role4 at reset0.
        word(expected,p+8,int(mode==1));word(expected,p+0x150,i+1 if mode==1 else i)
        raw=(first,second)[i] if mode==1 else f'GlobalPlayer{i}'.encode()+b'\0'
        expected[p+0x50:p+0x50+len(raw)]=raw
        for j in range(8):
            if i!=j:expected[p+0x18+j]=0;expected[j*0x154+0x18+i]=0
    result=call(u,0x4661c0,BASE,[])&255
    assert result==valid,(mode,count,selected)
    assert names==list(range(count) if valid and mode!=1 else [])
    assert bytes(u.mem_read(BASE,SIZE))==expected,(mode,count,selected,fill)
    assert struct.unpack('<I',u.mem_read(0x5fbf28,4))[0]==BASE
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0004
    return dict(mode=mode,count=count,selected=selected,fill=fill,result=result,
                formatted_slots=names,created_slots=list(created))

def verify():
    cases=[fixture(*v) for v in itertools.product((0,1,2,0xffffffff),(-1,0,1,2,7,8),(-1,0,1,6,7,8),(0,165,255))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='432 whole4661c0 cases. OnlyCRT sprintf doubled inmode!=1;mode1 nevercallsdouble,real465440/465500 used. Fullaa8 snapshots,return,stackcleanup/globalpointer. Mode1 ignorescount/selected,creates0/1 with4=0/8=1,index150=1/2,globalnames54/58 copied,aa0=-1. Othermodes requirecount1..7/selectedwithin,createcount slots4=0/8=0/index150=slot,actual4667c0 failsselection butinitializerreturnsAL1;aa0=-1. Invalidinputsresetall8andreturnAL0. Symmetric18 offdiagonalscleared forcreatedslots;diagonal1. Actualglobalsproducers,mode meaning,otherwriters/save/network andlocalization remainpending.')
    (ROOT/'modernization/docs/ai-profile-global-initializer-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),mode1_no_double=sum(c['mode']==1 for c in cases)))

if __name__=='__main__':verify()
