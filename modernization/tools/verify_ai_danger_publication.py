"""Native41d3a2 publication/resume slice with real map-copy/clear and lookup."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from verify_ai_danger_cell_effects import stage

def rotation(owner,mask,spent):
    u=machine();manager=0x2010000;units=0x2030000;sp=0x23e0000;visited=[];endpoint=[]
    for slot in range(8):
        put(u,0x643a80+slot*0x154,'II',int(bool(mask&(1<<slot))),0)
        put(u,0x643a80+slot*0x154+0xc,'I',0)
    put(u,manager+0x12099,'i',owner);put(u,manager+0x1209d,'I',999)
    put(u,0x6def58,'I',units);put(u,0x6def5c,'I',1)
    put(u,sp+0x38,'I',spent)
    def hook(uc,address,size,user):
        if address==0x41d4ae:visited.append(word(uc,manager+0x12099))
        if address in (0x41d505,0x41dc10):endpoint.append(address);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,manager)
    u.reg_write(UC_X86_REG_EBP,0);u.reg_write(UC_X86_REG_EBX,0)
    u.emu_start(0x41d476,0x2000000,count=100000)
    expected=[];current=owner;selected=None
    for _ in range(8-spent):
        current+=1
        if current==8:current=0
        expected.append(current)
        if mask&(1<<current):selected=current;break
    assert visited==expected
    assert word(u,manager+0x12099)==current&0xffffffff
    assert endpoint==[0x41d505 if selected is not None else 0x41dc10]
    assert word(u,sp+0x38)==spent+len(expected)
    assert word(u,manager+0x1209d)==(0 if selected is not None else 999)
    if selected is not None:assert word(u,manager+0x120a5)==units
    return dict(owner=owner,eligible_mask=mask,spent=spent,visited=visited,selected=selected)

def fixture(owner,count,start,native_finalizer=False):
    u=machine();manager=0x2010000;wizard=0x2030000;cells=0x2040000;sp=0x23e0000
    put(u,0x6eaf08,'III',cells,count,count);put(u,0x6eaf10,'I',count)
    put(u,0x6def58,'I',wizard);put(u,0x6def5c,'I',1)
    put(u,0x643a80+owner*0x154,'II',1,0);put(u,0x643a80+owner*0x154+0xc,'I',0)
    put(u,manager+0x12099,'i',owner);put(u,manager+0x120a1,'I',start)
    put(u,manager+0x120a9,'I',12345);put(u,wizard+0x926,'I',0x11223344)
    for i in range(count):
        u.mem_write(cells+i*0x294,b'\xa5'*0x294)
        if native_finalizer:put(u,cells+i*0x294+4,'3i',0,0,0)
    if native_finalizer:stage(u,[(69,0,10),(70,0,10),(91,0,10)],owner)
    else:u.mem_write(0x4202e0,b'\xc2\x08\x00')
    visited=[];endpoint=[]
    def hook(uc,address,size,user):
        if address in (0x41d476,0x41dc10):endpoint.append(address);uc.emu_stop();return
        if address!=0x4202e0:return
        s=uc.reg_read(UC_X86_REG_ESP);index,who=struct.unpack('<2I',uc.mem_read(s+4,8))
        assert who==owner and uc.reg_read(UC_X86_REG_ECX)==manager
        visited.append(index)
        if not native_finalizer:uc.mem_write(cells+index*0x294+0x28c,bytes((index+j+owner)&255 for j in range(7)))
    u.hook_add(UC_HOOK_CODE,hook)
    rounds=[]
    while True:
        before=word(u,manager+0x120a1);n=min(32,max(0,count-before));previous=len(visited)
        u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,manager);u.reg_write(UC_X86_REG_EBP,0)
        u.emu_start(0x41d3a2,0x2000000,count=200000)
        assert len(visited)-previous==n and visited[previous:]==list(range(before,before+n))
        complete=before+n>=count
        assert endpoint[-1]==(0x41d476 if complete else 0x41dc10)
        assert word(u,manager+0x120a1)==(0 if complete else before+n)
        assert word(u,wizard+0x926)==(12345 if complete else 0x11223344)
        assert word(u,manager+0x120a9)==(0 if complete else 12345)
        for i in range(count):
            scratch=bytes(u.mem_read(cells+i*0x294+0x28c,7))
            target=bytes(u.mem_read(cells+i*0x294+0x24c+owner*7,7))
            if complete:
                assert scratch==bytes(7)
                expected=(bytes([165,165,165,195,185,190,165]) if native_finalizer else bytes((i+j+owner)&255 for j in range(7))) if i>=start else b'\xa5'*7
                assert target==expected
            else:assert target==b'\xa5'*7
        rounds.append(dict(start=before,processed=n,published=complete))
        if complete:break
        assert len(rounds)<5
    return dict(owner=owner,cells=count,initial_cursor=start,rounds=rounds,native_finalizer=native_finalizer)

def verify():
    cases=[fixture(owner,count,start) for owner,count in itertools.product(range(8),(0,1,31,32,33,64,65)) for start in sorted({0,count//2,count})]
    rotations=[rotation(*v) for v in itertools.product(range(-1,8),(0,1,128,255,85,170),(0,7,8))]
    integrated=[fixture(owner,count,start,True) for owner,count in itertools.product(range(8),(0,1,32,33,65)) for start in sorted({0,count//2,count})]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,rotations=rotations,integrated=integrated,
        scope='144 native41d3a2..41d476 publication/resume fixtures with4202e0 doubled,real542be0/542ba0/466870;distinct per-cell bytes verify32 budget/deferred publication. 162 no-double41d476 rotation fixtures verify8-attempt budget/wrap/selection. Additional96 no-double publication fixtures use real4202e0 with synthetic type69/70/91 effect list through cell processing/publish/clear at all8 owners,count0/1/32/33/65,cursor0/middle/end. Full unit contribution loop,map field meanings,other profile exclusion/restart and scheduler caller timing pending.')
    (ROOT/'modernization/docs/ai-danger-publication-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),resume_rounds=sum(len(c['rounds']) for c in cases)))

if __name__=='__main__':verify()
