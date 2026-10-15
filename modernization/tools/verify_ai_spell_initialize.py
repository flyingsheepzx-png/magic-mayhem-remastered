"""Targeted spell initializer gates with real availability and group counters."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_spell_availability import setup
from verify_ai_training_math import put
from verify_ai_action_primitives import call
from verify_ai_groups import group,word
from verify_ai_model_native import ROOT,SHA

def fixture(action,spell,entry,count=1,parent=False,assigned=False,known=True,
            mana=20,powers=0,kind=0,wide=0,targets=1):
    u,caster=setup(cost=10,mana=mana*256,kind=kind,powers=powers)
    a=0x2100000;g=0x2110000;tg=0x2120000
    group(u,g,unit=caster);put(u,g,'I',count)
    put(u,g+0x39,'I',int(parent));put(u,g+5,'I',int(assigned))
    put(u,a+4,'I',action);put(u,a+0x149,'B',1)
    put(u,caster+0x95a,'i',wide)
    put(u,0x6b1270+spell*721,'I',10)
    put(u,0x6b13ed+spell*721+4*(2+2*8),'I',int(known))
    put(u,0x5d854c,'I',0)
    leaves=[0x2130000+i*0x400 for i in range(targets)]
    for i,leaf in enumerate(leaves):group(u,leaf,unit=0x2150000+i*0x1000)
    group(u,tg,children=leaves)
    u.mem_write(0x40f910,b'\xb8'+struct.pack('<I',tg)+b'\xc2\x04\0')
    u.mem_write(0x40f9e0,b'\xb8'+struct.pack('<I',tg)+b'\xc2\x04\0')
    builders=[]
    def inspect(uc,address,size,user):
        if address in [0x40f910,0x40f9e0]:
            builders.append([hex(address),word(uc,uc.reg_read(UC_X86_REG_ESP)+4)])
    u.hook_add(UC_HOOK_CODE,inspect)
    call(u,entry,a,[g,0,100])
    structural=count==1 and not parent and not assigned
    available=structural and known and kind in [0,24,25,26] and (mana>=10 or powers>0)
    eligible=available and targets>0
    assert bytes(u.mem_read(a+0x149,1))[0]==int(eligible)
    expected_builder='0x40f9e0' if wide and action!=44 else '0x40f910'
    assert builders==([[expected_builder,2]] if available else [])
    if available:
        assert word(u,a+0x14a)==caster and word(u,a+0x152)==tg
        expected_wait=0 if mana>=10 else ((10-mana+3*powers-1)//(3*powers))*20
        assert word(u,a+0x14e)==expected_wait
    if eligible:
        assert word(u,a+0x156)==0 and word(u,a+0x16)==130
        assert bytes(u.mem_read(tg+0x41,1))==b'\0'
    return dict(action_id=action,count=count,parent=parent,assigned=assigned,
                known=known,mana=mana,powers=powers,caster_kind=kind,wide=wide,
                targets=targets,eligible=eligible,builder=builders)

def verify():
    registry=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())
    spells={21:41,39:74,43:78,44:79,47:83,48:84,51:85,52:42}
    cases=[]
    for r in registry['actions']:
        action=r['action_id']
        if action not in spells:continue
        args=(action,spells[action],int(r['methods']['initialize'],16))
        for count,parent,assigned in itertools.product([0,1,2],[False,True],[False,True]):
            cases.append(fixture(*args,count=count,parent=parent,assigned=assigned))
        for known,mana,powers,kind,wide,targets in itertools.product([False,True],
                [5,20],[0,2],[0,1,24],[-1,0,1],[0,1,2]):
            cases.append(fixture(*args,known=known,mana=mana,powers=powers,
                                 kind=kind,wide=wide,targets=targets))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,action_ids=sorted(spells),
                scope='Full eight native initializers with real40a950/51e530/51e6c0,4078a0/407920 and40eff0. Only target-group builders40f910/40f9e0 doubled; group contents synthetic, so construction/visibility/alliance ownership invariants remain pending. No gameplay or player IO.')
    (ROOT/'modernization/docs/ai-spell-initialize-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',actions=8,cases=len(cases)))

if __name__=='__main__':verify()
