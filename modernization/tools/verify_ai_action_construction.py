"""Every registered native constructor and empty base-resource teardown."""
import json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from verify_ai_training_math import native
from capstone import Cs,CS_ARCH_X86,CS_MODE_32

def cleanup_map(rows):
    cs=Cs(CS_ARCH_X86,CS_MODE_32);result={}
    def instructions(va,size):return list(cs.disasm(native.image[va-native.base:va-native.base+size],va))
    for r in rows:
        ins=instructions(int(r['startup'],16),22)
        assert ins[0].mnemonic=='mov' and ins[0].op_str==f"ecx, {r['prototype']}"
        assert ins[1].mnemonic=='call' and int(ins[1].op_str,16)==int(r['constructor'],16)
        assert ins[2].mnemonic=='push' and ins[3].mnemonic=='call' and ins[3].op_str=='0x59b7e2'
        callback=int(ins[2].op_str,16);guard=instructions(callback,30)
        assert guard[6].mnemonic=='mov' and int(guard[6].op_str.split(', ')[1],16)==int(r['prototype'],16)
        assert guard[7].mnemonic=='jmp'
        result[r['action_id']]=dict(callback=hex(callback),cleanup=guard[7].op_str)
    return result

def fixture(rows,reverse=False,retreat_cleanup=False,populate_retreat_vectors=False,tree_nodes=0,tree_shape='balanced',all_derived=False):
    u=machine();u.mem_map(0,0x1000)
    for p in range(0x5faf20,0x5faf4c,4):put(u,p,'I',0)
    allocations={};released=set();bump=[0x2200000]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def allocator(uc,address,size,user):
        n=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
        if address==0x597850:
            p=bump[0];bump[0]+=(n+15)&~15
            assert bump[0]<0x23e0000
            allocations[p]=n;uc.reg_write(UC_X86_REG_EAX,p)
        elif address==0x597870 and n:
            assert n in allocations and n not in released,(hex(n),rows)
            released.add(n)
    u.hook_add(UC_HOOK_CODE,allocator)
    objects=[]
    for i,r in enumerate(rows):
        a=0x2010000+i*0x800
        result=call(u,int(r['constructor'],16),a,[])
        assert result==a and word(u,a)==int(r['vtable'],16)
        assert word(u,a+4)==r['action_id'] and word(u,a+0x23)==0xffffffff
        assert all(word(u,a+o)==0 for o in [0x3b,0x3f,0x43])
        if populate_retreat_vectors and r['action_id']==12:
            for offset in [0x16b,0x18f]:
                ptr=call(u,0x597850,0,[16])
                put(u,ptr,'4I',1,2,3,4);put(u,a+offset,'3I',ptr,ptr+16,ptr+16)
        if tree_nodes and r['action_id']==12:
            nil=word(u,0x5faf20);head=word(u,a+0x1a4)
            nodes=[call(u,0x597850,0,[20]) for _ in range(tree_nodes)]
            def build(lo,hi,parent):
                if lo==hi:return nil
                mid=(lo+hi)//2 if tree_shape=='balanced' else lo if tree_shape=='right' else hi-1
                node=nodes[mid];left=build(lo,mid,node);right=build(mid+1,hi,node)
                put(u,node,'5I',left,parent,right,mid+1,0)
                return node
            root=build(0,tree_nodes,head)
            put(u,head,'3I',nodes[0],root,nodes[-1]);put(u,a+0x1ac,'I',tree_nodes)
        objects.append(a)
    order=list(reversed(list(zip(objects,rows)))) if reverse else list(zip(objects,rows))
    mapping=cleanup_map(rows) if all_derived else {}
    for a,r in order:
        cleanup=int(mapping[r['action_id']]['cleanup'],16) if all_derived else 0x402330 if retreat_cleanup and r['action_id']==12 else 0x418050
        call(u,cleanup,a,[])
    remaining={hex(p):n for p,n in allocations.items() if p not in released}
    # Record additional constructor allocation ownership instead of assuming it
    # is a leak: derived resources require the actual derived cleanup path.
    if retreat_cleanup or all_derived:
        assert not remaining
        assert word(u,0x5faf20)==0 and word(u,0x5faf24)==0
    return dict(action_ids=[r['action_id'] for r in rows],reverse_order=reverse,
                retreat_full_cleanup=retreat_cleanup,
                all_derived_cleanup=all_derived,
                populated_retreat_vectors=populate_retreat_vectors,
                synthetic_retreat_tree_nodes=tree_nodes,synthetic_tree_shape=tree_shape,
                allocations=len(allocations),freed=len(released),remaining_after_base=remaining)

def verify():
    rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
    cases=[fixture([r]) for r in rows]
    cases.extend(fixture(rows,reverse) for reverse in [False,True])
    retreat=next(r for r in rows if r['action_id']==12)
    cases.extend(fixture([retreat]*n,reverse,True) for n in [1,2,5] for reverse in [False,True])
    cases.extend(fixture(rows,reverse,True) for reverse in [False,True])
    cases.extend(fixture([retreat]*n,reverse,True,True) for n in [1,2,5] for reverse in [False,True])
    cases.extend(fixture([retreat]*2,False,True,True,n,shape)
                 for n in [1,7,31] for shape in ['balanced','left','right'])
    mapping=cleanup_map(rows)
    cases.extend(fixture([r],all_derived=True) for r in rows)
    cases.extend(fixture(rows,reverse,all_derived=True) for reverse in [False,True])
    report=dict(engine_sha256=SHA,result='passed',cases=cases,prototype_cleanup_map=mapping,
                scope='All53 constructors/base teardown,Retreat full teardown including9 synthetic nonempty trees,all53 full prototype-derived cleanup functions individually and two mixed orders. CRT allocation/free sinks only. Empty-derived lifecycles and Retreat full-range tree freeing,not dynamic scheduler dispatch/insertion/balancing/partial erase/allocation failures.')
    (ROOT/'modernization/docs/ai-action-construction-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),additional_allocations=sum(len(c['remaining_after_base']) for c in cases)))

if __name__=='__main__':verify()
