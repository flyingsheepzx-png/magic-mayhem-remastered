"""Hash-gated native action commit transitions; no player process or game IO."""
import json, random, struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP
from verify_ai_training_math import machine, put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT, SHA
from verify_ai_groups import group, word

# Independently recovered mappings from per-action exports, checked against native
# execution over the entire object and both backing buffers (including sentinels).
BLOCKS = {
    5:(0x152,0x16e,7),16:(0x1b2,0x1ce,7),17:(0x162,0x17e,7),
    19:(0x162,0x17e,7),20:(0x166,0x182,7),22:(0x166,0x182,7),
    23:(0x15e,0x172,5),24:(0x15e,0x172,5),25:(0x15a,0x16e,5),
    26:(0x166,0x186,8),27:(0x16e,0x182,5),29:(0x166,0x182,7),
    31:(0x166,0x182,7),32:(0x16a,0x186,7),33:(0x166,0x182,7),
    34:(0x162,0x17e,7),35:(0x16a,0x186,7),36:(0x162,0x176,5),
    38:(0x162,0x176,5),40:(0x166,0x182,7),41:(0x162,0x17e,7),
    42:(0x15e,0x17a,7),45:(0x15a,0x16e,5),46:(0x166,0x186,8),
    49:(0x162,0x176,5),55:(0x16a,0x186,7),56:(0x166,0x182,7),
    57:(0x16b,0x17f,5),58:(0x156,0x17a,9),
}
SCALARS = {15:[(0x255,0x25d),(0x259,0x261)],
           18:[(0x162,0x16e),(0x166,0x172),(0x16a,0x176)],
           30:[(0x149,0x14d)],37:[(0x162,0x16a),(0x166,0x16e)],
           50:[(0x162,0x16e),(0x166,0x172),(0x16a,0x176)]}
for action in [21,39,43,44,47,48,51,52]:SCALARS[action]=[(0x15a,0x15e)]
NOOPS = {28,53,59}
# scalar source, scalar destination, count, vector source object, vector dest object
TACTICAL = {6:(0x153,0x16f,3,0x15f,0x17b),
            8:(0x193,0x1bb,6,0x1ab,0x1d3),
            9:(0x152,0x172,4,0x162,0x182),
            11:(0x153,0x17b,6,0x16b,0x193),
            12:(0x153,0x177,5,0x167,0x18b),
            13:(0x153,0x173,4,0x163,0x183),
            14:(0x158,0x170,2,0x160,0x178)}

def haste_fixture(count,repeat=False):
    u=machine();a=0x2010000;root=0x2020000;caster=0x2030000
    leaves=[0x2050000+i*0x200 for i in range(count)]
    u.mem_map(0x3000000,0x1000000)
    units=[0x3000000+i*0x1000 for i in range(count)]
    for i,(leaf,unit) in enumerate(zip(leaves,units)):
        group(u,leaf,unit=unit)
        put(u,unit+4,'I',int(i%5!=0));put(u,unit+0xe4,'I',0 if i%7==0 else 100)
        put(u,unit+0x174,'I',3 if i%3==0 else 2)
        put(u,unit+0x778,'I',int(i%11==0))
    group(u,root,children=leaves);put(u,caster+0x174,'I',2)
    put(u,a+0x166,'I',root);put(u,a+0x14a,'I',caster)
    put(u,a+0x19a,'I',0xffffffff);put(u,0x5d854c,'I',0)
    allocations=[];frees=[];bump=[0x2200000]
    u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
    def allocator(uc,address,length,user):
        arg=word(uc,uc.reg_read(UC_X86_REG_ESP)+4)
        if address==0x597850:
            ptr=bump[0];bump[0]+=(arg+15)&~15
            assert bump[0]<0x23e0000
            allocations.append(arg);uc.reg_write(UC_X86_REG_EAX,ptr)
        elif address==0x597870:frees.append(arg)
    u.hook_add(UC_HOOK_CODE,allocator)
    expected=[unit for i,unit in enumerate(units) if i%5!=0 and i%7!=0 and i%3!=0 and i%11!=0]
    def check():
        sp=0x23f0000;stop=0x2000000
        put(u,sp,'I',stop);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,a)
        u.emu_start(0x45df20,stop,count=1000000)
        assert u.reg_read(UC_X86_REG_EIP)==stop
        assert word(u,a+0x19a)==0 and word(u,a+0x196)==len(expected)
        actual=[];node=word(u,a+0x17a);lastnode=word(u,a+0x18a)
        cur=word(u,a+0x176);last=word(u,a+0x186)
        if node:
            while True:
                end=last if node==lastnode else word(u,node)+0x1000
                while cur!=end:
                    actual.append(word(u,cur));cur+=4
                    assert len(actual)<=count
                if node==lastnode:break
                node+=4;cur=word(u,node)
        assert actual==expected,(count,actual,expected)
    check()
    if repeat:
        for unit in units:put(u,unit+0x778,'I',1)
        expected=[];check()
        for i,unit in enumerate(units):put(u,unit+0x778,'I',int(i%11==0))
        expected=[unit for i,unit in enumerate(units) if i%5!=0 and i%7!=0 and i%3!=0 and i%11!=0]
        check()
    return dict(action_id=54,kind='haste_rebuild',unit_count=count,repeat_clear_and_rebuild=repeat,
                eligible_count=len(expected),allocation_sizes=allocations,free_calls=len(frees))

def verify():
    registry=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())
    entries={r['action_id']:int(r['methods']['commit_or_copy'],16) for r in registry['actions']}
    assert set(entries)==set(BLOCKS)|set(SCALARS)|NOOPS|set(TACTICAL)|{54}
    cases=[];a=0x2010000;rng=random.Random(0x4415e0)
    for action in sorted(set(BLOCKS)|set(SCALARS)|NOOPS):
        for fixture in range(12):
            u=machine();before=rng.randbytes(0x400);u.mem_write(a,before)
            expected=bytearray(before)
            if action in BLOCKS:
                src,dst,n=BLOCKS[action];expected[dst:dst+4*n]=before[src:src+4*n]
            else:
                for src,dst in SCALARS.get(action,[]):expected[dst:dst+4]=before[src:src+4]
            call(u,entries[action],a,[])
            assert bytes(u.mem_read(a,len(before)))==expected,(action,fixture)
            cases.append(dict(action_id=action,kind='whole_object_copy',fixture=fixture))
    layouts=[(0,0,0,True,True),(0,3,5,True,False),(0,3,5,False,False),
             (1,1,1,False,False),(2,5,8,False,False),(5,2,8,False,False),
             (8,0,8,False,False),(8,2,4,False,False),(4,0,0,False,True)]
    for action,(src,dst,n,sv,dv) in TACTICAL.items():
        for size,oldsize,capacity,nullsrc,nulldst in layouts:
            u=machine();u.mem_write(a,rng.randbytes(0x400))
            source=0x2020000;dest=0x2030000;fresh=0x2040000
            source_bytes=rng.randbytes(128);dest_bytes=rng.randbytes(128)
            u.mem_write(source,source_bytes);u.mem_write(dest,dest_bytes)
            u.mem_write(fresh,b'\xcd'*128)
            put(u,a+sv+4,'3I',0 if nullsrc else source,0 if nullsrc else source+size*4,0 if nullsrc else source+size*4)
            put(u,a+dv+4,'3I',0 if nulldst else dest,0 if nulldst else dest+oldsize*4,0 if nulldst else dest+capacity*4)
            before=bytes(u.mem_read(a,0x400));expected=bytearray(before)
            expected[dst:dst+4*n]=before[src:src+4*n]
            allocations=[];frees=[]
            reallocate=size>capacity
            # Only CRT allocation/free are replaced. All native vector helpers run.
            u.mem_write(0x597850,b'\xc3');u.mem_write(0x597870,b'\xc3')
            def allocator(uc,address,length,user):
                sp=uc.reg_read(UC_X86_REG_ESP)
                arg=struct.unpack('<I',uc.mem_read(sp+4,4))[0]
                if address==0x597850:
                    allocations.append(arg);uc.reg_write(UC_X86_REG_EAX,fresh)
                elif address==0x597870:frees.append(arg)
            u.hook_add(UC_HOOK_CODE,allocator)
            ptr=fresh if reallocate else (0 if nulldst else dest)
            struct.pack_into('<I',expected,dv+8,ptr+size*4)
            if reallocate:struct.pack_into('<3I',expected,dv+4,ptr,ptr+size*4,ptr+size*4)
            call(u,entries[action],a,[])
            assert bytes(u.mem_read(a,0x400))==expected,(action,size,oldsize,capacity)
            assert bytes(u.mem_read(source,128))==source_bytes
            if reallocate:
                assert allocations==[size*4] and frees==[0 if nulldst else dest]
                assert bytes(u.mem_read(dest,128))==dest_bytes
                assert bytes(u.mem_read(fresh,128))==source_bytes[:size*4]+b'\xcd'*(128-size*4)
            else:
                assert not allocations and not frees
                assert bytes(u.mem_read(dest,128))==source_bytes[:size*4]+dest_bytes[size*4:]
                assert bytes(u.mem_read(fresh,128))==b'\xcd'*128
            cases.append(dict(action_id=action,kind='vector_assignment',source_size=size,
                              old_size=oldsize,capacity=capacity,null_source=nullsrc,
                              null_destination=nulldst,allocation_bytes=allocations))
    cases.extend(haste_fixture(count,repeat) for count in [0,1,2,12,80,3000] for repeat in [False,True])
    report=dict(engine_sha256=SHA,result='passed',cases=cases,
                verified_action_ids=sorted(entries),
                pending_action_ids=[],
                block_mappings={str(i):v for i,v in BLOCKS.items()},
                scalar_mappings={str(i):v for i,v in SCALARS.items()},
                no_op_ids=sorted(NOOPS),tactical_mappings={str(i):v for i,v in TACTICAL.items()},
                scope='Full native commit methods for53 registered actions. Whole-object and backing-buffer assertions for copies; Haste54 real recursive iteration, eligibility gates, deque allocation and clear/rebuild. CRT allocation/free stubbed for allocation branches only. Target scoring, meaning of all copied fields and execution are not implied.')
    (ROOT/'modernization/docs/ai-commit-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',actions=53,cases=len(cases)))

if __name__=='__main__':verify()
