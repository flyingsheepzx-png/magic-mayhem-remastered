"""Native416590 early gates: whole refused calls, prefix admitted calls."""
import itertools,json
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA

def fixture(owner,wizard_present,unit_override,role,blocked,excluded_type,mode,local):
    u=machine();manager=0x2010000;unit=0x2020000;base=0x643a80
    u.mem_write(manager,b'\xa5'*0x100);u.mem_write(unit,bytes(0xe4b))
    u.mem_write(base,b'\xa5'*0xaa8)
    put(u,base+owner*0x154+4,'I',role);put(u,base+owner*0x154+12,'i',0 if wizard_present else -1)
    put(u,unit+0x174,'I',owner);put(u,unit+0x8e5,'I',unit_override)
    put(u,unit+0x704,'I',blocked);put(u,unit+0xa8,'I',22 if excluded_type else 0)
    put(u,0x6e1f0c,'i',mode);put(u,0x656634,'I',owner if local else (owner+1)%8)
    snapshots=[(a,n,bytes(u.mem_read(a,n))) for a,n in ((manager,0x100),(unit,0xe4b),(base,0xaa8))]
    admitted=(wizard_present or unit_override) and not role and not blocked and not excluded_type and (mode<=1 or local)
    sp=0x23f0000;stop=0x41660c if admitted else 0x2000000
    put(u,sp,'II',0x2000000,unit);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,manager)
    u.emu_start(0x416590,stop,count=1000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    if not admitted:assert u.reg_read(UC_X86_REG_ESP)==sp+8
    for a,n,raw in snapshots:assert bytes(u.mem_read(a,n))==raw
    return dict(owner=owner,wizard_present=wizard_present,unit_override=unit_override,role=role,
                blocked=blocked,excluded_type=excluded_type,mode=mode,local=local,admitted=bool(admitted))

def verify():
    cases=[fixture(*v) for v in itertools.product(range(8),(0,1),(0,1),(0,1,0xffffffff),(0,1),(0,1),(-1,0,1,2),(0,1))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='3072 native416590 entry-gate fixtures,no doubles. Refused cases executewhole function toreturn;admitted cases stop41660c beforegroup scan. All8validowners,profile+c missing/present,unit8e5 override,role4 zero/nonzero,unit704 block,typea8=22,mode-1/0/1/2 andlocalowner comparison. Manager/unit/profile snapshotsunchanged;refusedcallee pops4argumentbytes. Invalidowner andfulladmitted group creation/scheduler/save/network pending.')
    (ROOT/'modernization/docs/ai-unit-admission-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),admitted_prefix=sum(c['admitted'] for c in cases),whole_refused=sum(not c['admitted'] for c in cases)))

if __name__=='__main__':verify()
