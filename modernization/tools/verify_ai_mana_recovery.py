"""Native51d570/type19 use: item activation, mana clamp and deferred command."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(slot,quantity,route,mana,capacity,active=True,record_type=19):
    u=machine();unit=0x2010000;definition=0x2020000;items=0x2030000
    put(u,unit,'I',0x123);put(u,unit+0xac,'I',definition)
    put(u,definition,'I',0);put(u,unit+0x174,'I',2);put(u,0x644520,'I',3)
    put(u,unit+0xe8,'I',mana*256);put(u,unit+0xec,'I',capacity)
    record=unit+0x17c+slot*24
    put(u,record,'6I',record_type,10,0,0,quantity,int(active))
    put(u,unit+0x178,'I',int(active))
    put(u,0x6e1f0c,'i',route);put(u,0x6b1254,'I',20)
    put(u,0x6b1250,'I',items);put(u,items+19*32,'I',25)
    # Queue/effect sinks only; native scan, dispatch19 and507f00 execute intact.
    u.mem_write(0x537bd0,b'\xc2\x04\0');u.mem_write(0x564e90,b'\xc2\x18\0')
    packets=[];effects=[]
    def inspect(uc,address,size,user):
        sp=uc.reg_read(UC_X86_REG_ESP)
        if address==0x537bd0:
            p=word(uc,sp+4)
            packets.append(dict(header=word(uc,p),category=word(uc,p+4),
                                command=word(uc,p+8),unit_byte=bytes(uc.mem_read(p+12,1))[0],
                                item_slot=bytes(uc.mem_read(p+13,1))[0]))
        elif address==0x564e90:effects.append(list(struct.unpack('<6I',uc.mem_read(sp+4,24))))
    u.hook_add(UC_HOOK_CODE,inspect)
    before=bytes(u.mem_read(unit,0xe4b));call(u,0x51d570,unit,[])
    found=active and record_type==19
    deferred=found and route>1
    used=found and route<=1 and quantity>0
    expected_mana=min(capacity,mana+25) if used else mana
    assert word(u,unit+0xe8)==expected_mana*256
    assert word(u,record+16)==quantity-int(used)
    remains=active and not(used and quantity==1)
    assert word(u,record+20)==int(remains)
    assert word(u,unit+0x178)==int(remains)
    assert packets==([dict(header=0,category=8,command=14,unit_byte=0x23,item_slot=slot)] if deferred else [])
    assert effects==([[7,unit,19,0,0xffffffff,0xffffffff]] if used else [])
    if not used:assert bytes(u.mem_read(unit,0xe4b))==before
    return dict(slot=slot,quantity=quantity,route=route,mana=mana,capacity=capacity,
                active=active,record_type=record_type,deferred=deferred,used=used,
                mana_after=expected_mana,remaining_quantity=word(u,record+16))

def verify():
    cases=[fixture(*v) for v in itertools.product([0,5,41],[0,1,2],[-1,0,1,2],
                                                 [0,90],[100])]
    cases.extend(fixture(0,1,0,0,100,active=active,record_type=kind)
                 for active,kind in itertools.product([False,True],[18,19,20]))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='Full native51d570,468b10 type19 dispatch and507f00 mana changes. Effect564e90 and deferred command537bd0 are explicit sinks. Different-player owner excludes native UI update. Route6e1f0c meaning not promoted to multiplayer identity; player UI, packet delivery and actual spawned effects pending.')
    (ROOT/'modernization/docs/ai-mana-recovery-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
