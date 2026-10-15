"""Native41db06 tree walk and saturating two-channel accumulation; no doubles."""
import itertools,json
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA

def fixture(count,delta,initial,unit_state,aura=False):
    u=machine();manager=0x2010000;unit=0x2030000;cells=0x2040000
    head=0x2070000;nil=head+0x40;nodes=[head+0x100+i*32 for i in range(count)]
    put(u,0x5faf20,'I',nil);put(u,nil,'4I',nil,nil,nil,0)
    def make(lo,hi,parent):
        if lo==hi:return nil
        mid=(lo+hi)//2;node=nodes[mid]
        left=make(lo,mid,node);right=make(mid+1,hi,node)
        put(u,node,'4I',left,parent,right,cells+mid*0x294)
        return node
    root=make(0,count,head);put(u,head,'4I',nodes[0],root,nodes[-1],0)
    put(u,manager+0x1208c,'I',head);put(u,manager+0x120a5,'I',unit)
    put(u,unit+0x104,'I',unit_state)
    put(u,unit+0x114,'I',unit_state);put(u,0x6bcad6,'I',delta&0xffffffff)
    for i in range(count):
        u.mem_write(cells+i*0x294,bytes([initial])*0x294)
        put(u,cells+i*0x294+0x20c,'I',i%2)
    before=bytes(u.mem_read(cells,count*0x294));tree_before=bytes(u.mem_read(head,0x100+count*32))
    sp=0x23e0000;put(u,sp+0x34,'I',delta&0xffffffff);put(u,sp+0x14,'I',nodes[0])
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,manager);u.reg_write(UC_X86_REG_EAX,nodes[0])
    u.reg_write(UC_X86_REG_EBP,0);u.reg_write(UC_X86_REG_ESI,255)
    end=0x41d8a3 if aura else 0x41dba3
    u.emu_start(0x41d836 if aura else 0x41db06,end,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==end
    expected=bytearray(before)
    raw=(initial+delta)&0xffffffff;signed=raw if raw<0x80000000 else raw-0x100000000
    value=min(255,max(0,signed))
    for i in range(count):
        if aura:
            if unit_state:expected[i*0x294+0x28e]=value
        else:
            expected[i*0x294+0x28c]=value
            if i%2==0 or unit_state:expected[i*0x294+0x28d]=value
    assert bytes(u.mem_read(cells,count*0x294))==bytes(expected)
    assert bytes(u.mem_read(head,0x100+count*32))==tree_before
    return dict(cells=count,delta=delta,initial=initial,unit_state=unit_state,clamped=value,aura_branch=aura)

def verify():
    cases=[fixture(*v) for v in itertools.product((1,3,7,31),(-300,-1,0,1,30,255,300,0x7fffffff),(0,128,250,255),(0,1),(False,True))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='512 no-double slices:256 native41db06..41dba3 generic accumulation,256 native41d836..41d8a3 unit114-dependent auxiliary accumulation,actual42d7d0 successor through balanced synthetic map-cell trees. Signed32 wrapping followed clamp0..255 updates28c always,28d iff cell20c zero or unit104 nonzero;auxiliary28e adds global6bcad6 iff unit114 nonzero with ESI=255/EBP=0. All cell bytes and unchanged tree compared;1/3/7/31 entries,negative/positive/overflow contribution fixtures. Contribution origin/tree construction/other map branches/full41d270 integration pending;negative deltas are injected arithmetic fixtures,not production observations.')
    (ROOT/'modernization/docs/ai-danger-map-accumulation-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
