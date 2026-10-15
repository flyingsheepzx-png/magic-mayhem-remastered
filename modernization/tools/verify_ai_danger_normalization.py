"""Native41d505 contribution normalization and branch gate, real411e50."""
import itertools,json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(kind,status,mode18,override,definition34,aux,raw,extra):
    u=machine();manager=0x2010000;unit=0x2030000;definition=0x2040000;cells=0x2050000;sp=0x23e0000;end=[]
    put(u,manager+0x120a5,'I',unit);put(u,unit+0xac,'I',definition)
    put(u,definition,'I',kind);put(u,definition+0x34,'I',definition34)
    put(u,unit+0xde7,'I',1);put(u,0x6eaf08,'I',cells);put(u,0x6eaf0c,'I',2)
    for offset,value in ((0x7c,status),(0xa8,18 if mode18 else 0),(0x108,override),(0x114,aux),(0xe8,raw),(0x91e,extra)):
        put(u,unit+offset,'I',value)
    def hook(uc,address,size,user):
        if address in (0x41d5af,0x41d8a3):end.append(address);uc.emu_stop()
    handle=u.hook_add(UC_HOOK_CODE,hook)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EDI,manager);u.reg_write(UC_X86_REG_EBP,0)
    u.emu_start(0x41d505,0x2000000,count=100000)
    expected=((((raw&0xffffff00)+extra)&0xffffffff)*20&0xffffffff)//10000
    actual=word(u,sp+0x34);assert actual==expected
    assert word(u,sp+0x24)==cells+0x294
    branch=bool((kind in (0,24,25,26) and status==0) or (definition34 and not(mode18 and override)) or aux)
    assert end==[0x41d5af if branch else 0x41d8a3]
    u.hook_del(handle);second=[]
    def hook_second(uc,address,size,user):
        if address in (0x41d8fd,0x41dba3):second.append(address);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook_second)
    u.reg_write(UC_X86_REG_EDI,manager);put(u,sp+0x1c,'I',manager)
    u.emu_start(0x41d8a3,0x2000000,count=100000)
    second_branch=bool(not(kind in (0,24,25,26) and status==0) and ((mode18 and override) or not definition34))
    assert second==[0x41d8fd if second_branch else 0x41dba3]
    return dict(kind=kind,status=status,mode18=mode18,override=override,definition34=definition34,aux=aux,raw_e8=raw,extra91e=extra,normalized=actual,first_map_branch=branch,second_map_branch=second_branch)

def verify():
    payloads=((0,0),(255,1),(256,0),(10000,256),(0xffffffff,0),(0xffffffff,0x7fffffff))
    cases=[fixture(*v,*payload) for v in itertools.product((0,24,25,26,1,2),(0,1),(0,1),(0,1),(0,1),(0,1)) for payload in payloads]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='1152 no-double41d505 normalization/first-gate fixtures plus1152 separately staged41d8a3 second-gate executions with real411e50. Unit cell pointer mapping,quantized e8+91e modulo32 then multiply20 modulo32 unsigned floor division10000. Wizard shortcut/status,definition34,a8=18/108 override,unit114 first-path admission;second branch complementary primary rule,unit114 independent. Unsigned overflow payloads;map tree construction/intervening branches/field producer names/whole41d270 pending.')
    (ROOT/'modernization/docs/ai-danger-normalization-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
