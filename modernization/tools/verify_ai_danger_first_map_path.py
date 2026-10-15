"""Integrated41d505 first map path: native graph selection/tree/accumulation."""
import itertools,json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

GRAPHS=(((0,1),(1,2),(2,3)),((0,1),(0,2),(1,3),(2,3)),())

def fixture(graph,gate,channel,raw,initial,aura,repeats=1):
    u=machine();u.mem_map(0,4096);m=0x2010000;unit=0x2030000;definition=0x2040000;cells=0x2050000
    head=0x2070000;nil=head+0x40;sp=0x23e0000;bump=[0x2100000];allocated=[];freed=set()
    put(u,nil,'5I',nil,nil,nil,0,1);put(u,head,'5I',head,nil,head,0,0)
    put(u,0x5faf20,'I',nil);put(u,m+0x1208c,'I',head)
    put(u,m+0x120a5,'I',unit);put(u,unit+0xac,'I',definition);put(u,definition,'I',0)
    put(u,unit+0xde7,'I',0);put(u,unit+0xe8,'I',raw);put(u,unit+0x114,'I',aura)
    put(u,0x6bcad6,'I',30);put(u,0x6eaf08,'I',cells);put(u,0x6eaf0c,'I',4)
    for i in range(4):u.mem_write(cells+i*0x294+0x28c,bytes([initial])*7)
    slots={}
    for src,dst in graph:
        slot=slots.get(src,0);slots[src]=slot+1;edge=cells+src*0x294+0x10+slot*28
        put(u,edge,'II',1,dst);put(u,edge+(8 if channel==0 else 11),'BB',1,gate)
    before=bytes(u.mem_read(cells,4*0x294));u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def hook(uc,address,size,user):
        if address==0x597850:
            n=word(uc,uc.reg_read(UC_X86_REG_ESP)+4);assert n==20
            p=bump[0];bump[0]+=32;allocated.append(p);uc.reg_write(UC_X86_REG_EAX,p)
        elif address==0x597870:
            p=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
            assert p in allocated and p not in freed;freed.add(p)
    u.hook_add(UC_HOOK_CODE,hook)
    normalized=((raw&0xffffff00)*20&0xffffffff)//10000
    expected=bytearray(before);rounds=[]
    for repeat in range(repeats):
        start=0 if repeat%2==0 else 3;put(u,unit+0xde7,'I',start)
        old_live=set(allocated)-freed
        put(u,sp+0x1c,'I',m);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,m);u.reg_write(UC_X86_REG_EBP,0)
        u.emu_start(0x41d505,0x41d8a3,count=500000)
        assert u.reg_read(UC_X86_REG_EIP)==0x41d8a3
        expected_set={start}
        if 0<gate<128:
            first={dst for src,dst in graph if src==start};expected_set|=first
            expected_set|={dst for src,dst in graph if src in first}
        seen=[];nodes=set()
        def inspect(node,parent):
            if node==nil:return 1
            assert node not in nodes;nodes.add(node)
            assert word(u,node+4)==parent
            left=inspect(word(u,node),node);seen.append(word(u,node+0xc));right=inspect(word(u,node+8),node)
            assert left==right
            color=word(u,node+0x10);assert color in (0,1)
            if color==0:assert word(u,word(u,node)+0x10)==word(u,word(u,node+8)+0x10)==1
            return left+color
        root=word(u,head+4);assert word(u,root+0x10)==1;inspect(root,head)
        assert seen==[cells+i*0x294 for i in sorted(expected_set)],(graph,gate,repeat,start,seen,sorted(expected_set),len(freed))
        assert old_live<=freed and set(allocated)-freed==nodes
        assert len(nodes)==word(u,m+0x12094)==len(expected_set)
        for i in expected_set:
            for offset in (0x28c,0x28d):
                p=i*0x294+offset;expected[p]=min(255,expected[p]+normalized)
            if aura:
                p=i*0x294+0x28e;expected[p]=min(255,expected[p]+30)
        assert bytes(u.mem_read(cells,4*0x294))==bytes(expected)
        assert u.reg_read(UC_X86_REG_ESI)==255 and u.reg_read(UC_X86_REG_EBP)==0
        rounds.append(dict(start=start,selected=sorted(expected_set),freed_nodes=len(freed)))
    return dict(graph=graph,gate=gate,channel=channel,raw=raw,initial=initial,aura=aura,selected=sorted(expected_set),normalized=normalized,allocated_nodes=len(allocated),freed_nodes=len(freed),rounds=rounds)

def verify():
    cases=[fixture(*v) for v in itertools.product(GRAPHS,(0,1,255),(0,1),(0,256,8192,0xffffffff),(0,250),(0,1))]
    repeated=[fixture(graph,gate,channel,8192,initial,aura,3) for graph,gate,channel,initial,aura in itertools.product(GRAPHS,(0,1,255),(0,1),(0,250),(0,1))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,repeated=repeated,
        scope='288 initial and72 three-round native41d505..41d8a3 first-map-path fixtures;onlyCRT allocation/free doubled. Real normalization/411e50,uniqueRBtree graph selection/accumulation and native42e440/4298e0/42fde0/42acc0 oldtree cleanup. Three-round starts0/3/0:previous nodes freed once,currenttreeexact,no stale selection,cellchannels retain/add contributions. Wizard type0/status0,chain/diamond/disconnected,signed gates,two adjacency channels,fullcell/RB/allocation ownership assertions. Other unit types/secondpath reload/whole41d270 pending.')
    (ROOT/'modernization/docs/ai-danger-first-map-path-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
