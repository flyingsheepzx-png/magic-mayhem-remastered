"""Native group detach/destruction and action-owned group cleanup."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import group,word
from verify_ai_model_native import ROOT,SHA

def detach(index,cursor,free,missing=False,leaf=False):
    u=machine();g=0x2010000;children=[g+0x400+i*0x400 for i in range(3)]
    for c in children:group(u,c);put(u,c+0x39,'I',g)
    group(u,g,children=children,unit=0x2020000 if leaf else 0)
    begin=g+0x100;put(u,g+0x49,'I',begin+cursor*4)
    put(u,g+0x41,'B',free)
    target=g+0x1800 if missing else children[index]
    if missing:group(u,target);put(u,target+0x39,'I',g)
    before=bytes(u.mem_read(g,0x2000));call(u,0x407780,g,[target])
    changed=not missing and not leaf
    expected=[c for i,c in enumerate(children) if not changed or i!=index]
    assert word(u,g+0x2d)==begin+len(expected)*4
    assert [word(u,begin+i*4) for i in range(len(expected))]==expected
    assert word(u,g+0x49)==begin+(cursor-int(changed and not free and index<cursor))*4
    assert word(u,target+0x39)==(0 if changed else g)
    if not changed:assert bytes(u.mem_read(g,0x2000))==before
    return dict(kind='detach',index=index,cursor=cursor,free=free,missing=missing,leaf=leaf)

def destruction(cutoff,rank):
    u=machine();u.mem_map(0,0x1000)
    parent=0x2010000;g=parent+0x400;children=[g+0x400,g+0x800]
    group(u,parent,children=[g]);group(u,g,children=children)
    put(u,g+0x39,'I',parent)
    for c in children:group(u,c,unit=0x2030000,rank=rank);put(u,c+0x39,'I',g)
    put(u,0x5d854c,'i',cutoff);frees=[]
    u.mem_write(0x597870,b'\xc3')
    def inspect(uc,address,size,user):
        if address==0x597870:frees.append(word(uc,uc.reg_read(UC_X86_REG_ESP)+4))
    u.hook_add(UC_HOOK_CODE,inspect)
    call(u,0x407650,g,[])
    assert frees==[g+0x100]
    assert word(u,0x5d854c)==cutoff
    assert all(word(u,g+o)==0 for o in [0x29,0x2d,0x31,0x39])
    assert word(u,parent+0x2d)==word(u,parent+0x29)
    # Destructor resets cutoff to0 temporarily; negative-rank leaf children skip.
    assert all(word(u,c+0x39)==(0 if rank>=0 else g) for c in children)
    return dict(kind='group_destructor',cutoff=cutoff,child_rank=rank,freed=frees)

def action_cleanup(reverse=False):
    u=machine();u.mem_map(0,0x1000)
    a=0x2010000;g=a+0x1000;children=[g+0x400,g+0x800];owned=a+0x3000
    group(u,g,children=children)
    for c in children:group(u,c,unit=0x2050000,rank=3);put(u,c+0x39,'I',g)
    groups=children+[g] if reverse else [g]+children
    put(u,owned,'3I',*groups);put(u,a+0x3b,'3I',owned,owned+12,owned+12)
    put(u,0x5d854c,'I',5);frees=[]
    u.mem_write(0x597870,b'\xc3')
    def inspect(uc,address,size,user):
        if address==0x597870:frees.append(word(uc,uc.reg_read(UC_X86_REG_ESP)+4))
    u.hook_add(UC_HOOK_CODE,inspect)
    # Validate the owned-group destruction prefix only. Remaining feature-tree
    # destructors need properly constructed heads and are outside this fixture.
    u.reg_write(UC_X86_REG_ECX,a);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x418050,0x4180c9,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x4180c9
    assert word(u,a)==0x5c5358 and word(u,0x5d854c)==5
    assert word(u,a+0x3b)==owned and word(u,a+0x3f)==owned
    assert all(word(u,c+0x39)==0 for c in children)
    for ptr in groups+[g+0x100]:assert frees.count(ptr)==1,(ptr,frees)
    assert owned not in frees
    assert all(word(u,c+0x35)==0x2050000 for c in children)
    return dict(kind='base_action_owned_group_cleanup_prefix',child_first=reverse,freed=frees)

def constructed_cleanup(action_count,reverse=False,with_groups=False):
    u=machine();u.mem_map(0,0x1000)
    # Fresh emulated subsystem, not executable startup's stale initialized heads.
    for p in range(0x5faf2c,0x5faf4c,4):put(u,p,'I',0)
    allocations={};released=set();events=[];bump=[0x2200000]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def allocator(uc,address,size,user):
        arg=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
        if address==0x597850:
            ptr=bump[0];bump[0]+=(arg+15)&~15
            assert bump[0]<0x23e0000
            allocations[ptr]=arg;uc.reg_write(UC_X86_REG_EAX,ptr)
        elif address==0x597870 and arg:
            assert arg in allocations and arg not in released,(hex(arg),released)
            released.add(arg);events.append(arg)
    u.hook_add(UC_HOOK_CODE,allocator)
    actions=[0x2010000+i*0x1000 for i in range(action_count)]
    for a in actions:
        assert call(u,0x422ec0,a,[])==a
        assert word(u,a)==0x5c58fc and word(u,a+4)==5
        assert word(u,a+0x23)==0xffffffff
        if with_groups:
            root=call(u,0x419990,a,[])
            leaf=call(u,0x419a10,a,[0x2100000])
            call(u,0x407710,root,[leaf])
    # Shared sentinels persist while other actions remain alive.
    ordered=list(reversed(actions)) if reverse else actions
    for i,a in enumerate(ordered):
        call(u,0x418050,a,[])
        assert all(word(u,a+o)==0 for o in [0x3b,0x3f,0x43])
        for count in [0x5faf30,0x5faf38,0x5faf48]:
            assert word(u,count)==action_count-i-1
        if i+1<action_count:
            for ptr in [0x5faf2c,0x5faf34,0x5faf44]:
                assert word(u,ptr) and word(u,ptr) not in released
    assert released==set(allocations),(allocations,released)
    assert all(word(u,p)==0 for p in [0x5faf2c,0x5faf34,0x5faf44])
    return dict(kind='native_constructor_full_base_destructor',action_count=action_count,
                reverse_order=reverse,with_native_groups=with_groups,
                allocations=len(allocations),non_null_frees=len(events))

def verify():
    cases=[detach(*v) for v in itertools.product(range(3),range(4),[False,True])]
    cases.extend([detach(0,2,False,missing=True),detach(0,2,False,leaf=True)])
    cases.extend(destruction(*v) for v in itertools.product([0,5],[-1,0,3]))
    cases.extend(action_cleanup(reverse) for reverse in [False,True])
    cases.extend(constructed_cleanup(*v) for v in itertools.product([1,2,5],[False,True],[False,True]))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='Full native407780/407650, action prefix and12 constructed lifecycle cases: real422ec0 and full418050, shared feature-tree sentinels, empty containers and native owned groups. CRT allocation/free sinks only; allocations all released exactly once. Nonempty feature trees, derived destructors and allocation failures pending.')
    (ROOT/'modernization/docs/ai-group-cleanup-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
