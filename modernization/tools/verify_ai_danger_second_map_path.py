"""Integrated native41d505 second map path, native descriptor/tree/accumulation."""
import itertools,json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from verify_ai_danger_first_map_path import GRAPHS

def fixture(graph,channel,gate,mode,required,unit_state,blocked,minimum=1):
    u=machine();u.mem_map(0,4096);m=0x2010000;unit=0x2030000;definition=0x2040000;cells=0x2050000
    head=0x2070000;nil=head+0x40;sp=0x23e0000;bump=[0x2100000];allocated=[]
    put(u,nil,'5I',nil,nil,nil,0,1);put(u,head,'5I',head,nil,head,0,0)
    put(u,0x5faf20,'I',nil);put(u,m+0x1208c,'I',head);put(u,m+0x120a5,'I',unit)
    put(u,unit+0xac,'I',definition);put(u,definition,'I',1)
    put(u,definition+8,'II',1,required);put(u,definition+0x44,'I',mode)
    put(u,unit+0xe8,'I',8192);put(u,unit+0x104,'I',unit_state)
    put(u,0x6eaf08,'I',cells);put(u,0x6eaf0c,'I',4)
    for i in range(4):put(u,cells+i*0x294+0x20c,'I',blocked)
    offsets=(8,11,14,17,20);slots={}
    for src,dst in graph:
        slot=slots.get(src,0);slots[src]=slot+1;edge=cells+src*0x294+0x10+slot*28
        put(u,edge,'II',1,dst);offset=offsets[channel]
        put(u,edge+offset,'BB',1,gate)
        if channel==4:put(u,edge+offset+3,'B',minimum)
    before=bytes(u.mem_read(cells,4*0x294));u.mem_write(0x597850,b'\xc3')
    def hook(uc,address,size,user):
        if address==0x597850:
            assert word(uc,uc.reg_read(UC_X86_REG_ESP)+4)==20
            p=bump[0];bump[0]+=32;allocated.append(p);uc.reg_write(UC_X86_REG_EAX,p)
    u.hook_add(UC_HOOK_CODE,hook);put(u,sp+0x1c,'I',m)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,m);u.reg_write(UC_X86_REG_EBP,0)
    u.emu_start(0x41d505,0x41dba3,count=500000)
    assert u.reg_read(UC_X86_REG_EIP)==0x41dba3
    signed_gate=gate if gate<128 else gate-256
    accepted=(channel==0 or (channel==1 and unit_state) or
        (channel==2 and mode==2) or (channel==3 and mode==3) or (channel==4 and mode==1)) and signed_gate>=required
    if channel==4:accepted=accepted and minimum<=required
    selected={0}|({dst for src,dst in graph if src==0} if accepted else set())
    seen=[]
    def inspect(node,parent):
        if node==nil:return 1
        assert word(u,node+4)==parent
        left=inspect(word(u,node),node);seen.append(word(u,node+0xc));right=inspect(word(u,node+8),node)
        assert left==right;black=word(u,node+0x10);assert black in (0,1)
        if not black:assert word(u,word(u,node)+0x10)==word(u,word(u,node+8)+0x10)==1
        return left+black
    root=word(u,head+4);assert word(u,root+0x10)==1;inspect(root,head)
    assert seen==[cells+i*0x294 for i in sorted(selected)]
    assert word(u,m+0x12094)==len(allocated)==len(selected)
    expected=bytearray(before)
    for i in selected:
        expected[i*0x294+0x28c]=16
        if not blocked or unit_state:expected[i*0x294+0x28d]=16
    assert bytes(u.mem_read(cells,4*0x294))==bytes(expected)
    return dict(graph=graph,channel=channel,gate=gate,mode=mode,required=required,unit_state=unit_state,blocked=blocked,minimum=minimum,selected=sorted(selected))

def verify():
    cases=[fixture(*v) for v in itertools.product(GRAPHS,(0,1,2,3,4),(0,1,2,255),(0,1,2,3),(1,2),(0,1),(0,1))]
    cases.extend(fixture(graph,4,gate,mode,required,unit_state,blocked,3)
        for graph,gate,mode,required,unit_state,blocked in itertools.product(GRAPHS,(0,1,2,255),(0,1,2,3),(1,2),(0,1),(0,1)))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='2304 native41d505..41dba3 second-map-path integrations,onlyCRT allocation doubled. Type1,definition34=0,114=0,capability index1/required1or2;actual normalization/411e50/40e250/movement-specific neighbor selection/unique pointer RB insertion/successor/conditional28c-28d accumulation. Channel18/1b/1e/21/24 flags,byte thresholds0/1/2/255,modes0..3,mode1 minimum1/3,unit104 andcell20c;chain/diamond/disconnected,fullcell/RB assertions. Only owncell+onehop admitted,not firstpath twohop. Wider capability index/other unit states/reload/full41d270 pending.')
    (ROOT/'modernization/docs/ai-danger-second-map-path-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
