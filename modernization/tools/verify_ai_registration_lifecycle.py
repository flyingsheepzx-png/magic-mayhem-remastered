"""Whole4289e0 registration chain with real group, tree, prepare and factory."""
import json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_action_lookup import tree
from verify_ai_groups import group,word
from verify_ai_model_native import ROOT,SHA
from verify_ai_training_math import native
from capstone import Cs,CS_ARCH_X86,CS_MODE_32

MODE_FIELDS={21:0x6b873a,39:0x6be42b,44:0x6bf240,47:0x6bfd84,52:0x6b8a0b}
SPELL_IDS=(21,39,43,44,47,48,51,52)

def fixture(mode,missing,count,action_id=59):
    rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
    row=next(r for r in rows if r['action_id']==action_id)
    u=machine();u.mem_map(0,0x1000)
    for p in range(0x5faf20,0x5faf4c,4):put(u,p,'I',0)
    allocations={};freed=set();bump=[0x2200000]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def inspect(uc,address,size,user):
        if address not in (0x597850,0x597870):return
        n=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
        if address==0x597850:
            ptr=bump[0];bump[0]+=(n+15)&~15;assert bump[0]<0x23e0000
            allocations[ptr]=n;uc.reg_write(UC_X86_REG_EAX,ptr)
        elif n:
            assert n in allocations and n not in freed;freed.add(n)
    u.hook_add(UC_HOOK_CODE,inspect)
    m=0x2010000;slot=0x2040000;pool=0x2050000;arena=0x2091000
    head=tree(u,m,[],arena);put(u,m+0xc6,'I',0)
    put(u,m+0x11fe5,'I',slot);put(u,m+0xca,'I',0)
    put(u,0x6def58,'I',pool);put(u,0x6def5c,'I',1)
    put(u,0x643a80+2*0x154,'I',int(not missing));put(u,0x643a80+2*0x154+12,'I',0)
    put(u,pool+0x174,'I',2);put(u,pool+0x922,'ii',100,999)
    if action_id in SPELL_IDS:
        if action_id in MODE_FIELDS:
            entry=int(row['methods']['prepare_execute'],16)
            ins=list(Cs(CS_ARCH_X86,CS_MODE_32).disasm(native.image[entry-native.base:entry-native.base+100],entry))
            assert any(hex(MODE_FIELDS[action_id]) in i.op_str for i in ins)
            put(u,MODE_FIELDS[action_id],'I',3)
        put(u,0x6c549c,'I',0);put(u,0x5e147c,'I',0)
        put(u,pool+0xac,'I',pool+0x3000);put(u,pool+0x3000+0x19c,'I',12)
        put(u,pool+0x1c,'I',0)
    put(u,0x5d854c,'i',0)
    source=call(u,int(row['methods']['clone'],16),0,[]);put(u,slot,'I',source)
    registered=[]
    for index in range(count):
        if action_id in SPELL_IDS:
            put(u,source+0x15e,'I',pool);put(u,source+0x14e,'I',index)
            put(u,source+0x162,'B',1)
        g=0x20a0000+index*0x200;group(u,g,unit=pool,rank=3)
        put(u,m+0x14,'I',100+index);put(u,m+0x11ddc,'B',mode);put(u,m+0x11ddd,'f',.5)
        call(u,0x4289e0,m,[g])
        assert word(u,g+5)==source and word(u,source+8)==g
        duration=40 if action_id==59 else index+(9 if action_id==39 else 6)
        assert word(u,source+0xc)==100+index and word(u,source+0x10)==100+index+duration
        assert word(u,source+0x1f)==index and word(u,source+0x27)==2
        assert bytes(u.mem_read(source+0x1a,1))==bytes([mode])
        assert word(u,source+0x2f)==word(u,source+0x33)==0
        if action_id in SPELL_IDS:assert bytes(u.mem_read(source+0x162,1))==b'\0'
        registered.append(source)
        source=word(u,slot);assert source!=registered[-1] and source in allocations
        assert word(u,source+4)==action_id and word(u,source+0x23)==0xffffffff
        assert word(u,m+0xca)==index+1 and word(u,m+0xc6)==index+1
        for key,value in enumerate(registered):assert call(u,0x416c30,m,[key])==value
    assert call(u,0x416c30,m,[count])==0
    # Verify actual insertion's tree shape, parent links and red/black invariants.
    nil=word(u,0x5faf50);root=word(u,head+4);seen=[]
    def visit(node,parent):
        if node==nil:return 1
        assert word(u,node+4)==parent
        left=word(u,node);right=word(u,node+8);color=word(u,node+0x14)
        assert color in (0,1)
        if color==0:assert word(u,left+0x14)==word(u,right+0x14)==1
        lh=visit(left,node);seen.append(word(u,node+0xc));rh=visit(right,node)
        assert lh==rh
        return lh+color
    assert word(u,root+0x14)==1;visit(root,head);assert seen==list(range(count))
    return dict(action_id=action_id,mode=mode,missing_wizard=missing,registered=count,allocations=len(allocations),freed_buffers=len(freed),tree_keys=seen)

def verify():
    cases=[fixture(mode,missing,count) for mode in (0,1) for missing in (False,True) for count in (1,2,8,32)]
    cases.extend(fixture(mode,missing,count,action) for action in SPELL_IDS for mode in (0,1) for missing in (False,True) for count in (1,2,8,32))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole4289e0 for59 and eight targeted spells21/39/43/44/47/48/51/52:actual native prepare/factory,group cursor/owner,466870,42b210/42da70 tree insertion and balancing plus416c30 lookup. Conditional prepares use verified global mode3; real464c50 where called and synthetic target geometry. CRT allocation/free doubled only. Synthetic initial empty tree,one-unit groups; constructors/group state setup explicit. No manager/action destruction,other prepare modes,duplicate IDs or allocator failures covered.')
    (ROOT/'modernization/docs/ai-registration-lifecycle-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),registrations=sum(c['registered'] for c in cases)))

if __name__=='__main__':verify()
