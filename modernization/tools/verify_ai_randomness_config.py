"""Four native randomness config assignment slices; Win32 string API doubled."""
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put,native
from verify_ai_model_native import ROOT,SHA

SLICES=[(0x4e775c,0x4e7792,0x5e3630),(0x4e78d6,0x4e790c,0x5e35bc),(0x4e7a50,0x4e7a86,0x5e3548),(0x4e7bca,0x4e7c00,0x5e34d4)]

def fixture(index,text,expected):
    u=machine();api=0x2003000;sp=0x23f0000;target=0x6e200c+4*index
    put(u,target,'i',37);u.mem_write(api,b'\xc2\x18\x00')
    start,stop,key=SLICES[index];seen=[]
    def capture(uc,address,size,user):
        if address!=api:return
        args=struct.unpack('<6I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP)+4,24))
        assert args==(0x5e3694,key,0x5faf28,0x6e2a88,256,0x6e2780)
        seen.append(args);data=text.encode('ascii');uc.mem_write(0x6e2a88,data+b'\0');uc.reg_write(UC_X86_REG_EAX,len(data))
    u.hook_add(UC_HOOK_CODE,capture);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EBP,api)
    u.emu_start(start,stop,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop and len(seen)==1
    value=struct.unpack('<i',u.mem_read(target,4))[0];assert value==expected,(text,value,expected)
    return dict(index=index,text=text,value=value)

def verify():
    cases=[fixture(i,text,value) for i in range(4) for text,value in [('',37),('0',0),('60',60),('15',15),('-1',-1),('101',101),('  +50rest',50),('invalid',0)]]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Native four DIFFICULTY/AIRandomness0..3 assignment slices with real59c5a4 integer conversion. GetPrivateProfileStringA explicit double; disk config/whole initialization/Windows file semantics excluded. Missing value preserves prior37,invalid nonempty becomes0; no range clamp.')
    (ROOT/'modernization/docs/ai-randomness-config-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
