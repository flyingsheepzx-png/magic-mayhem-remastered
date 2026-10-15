"""Native command-token slices; real case-insensitive compare and integer parse."""
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_model_native import ROOT,SHA

def difficulty(key,value,expected):
    u=machine();k=0x2010000;v=k+256;sp=0x23f0000
    u.mem_write(k,key.encode()+b'\0');u.mem_write(v,value.encode()+b'\0')
    put(u,0x689924,'i',37);put(u,0x6fa2e8,'I',0)
    u.reg_write(UC_X86_REG_ESI,k);u.reg_write(UC_X86_REG_EBP,v);u.reg_write(UC_X86_REG_ESP,sp)
    reached=[]
    def capture(uc,address,size,user):
        if address in [0x4e8534,0x4e8929]:reached.append(address);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,capture)
    u.emu_start(0x4e8904,0x4e8946,count=100000)
    actual=struct.unpack('<i',u.mem_read(0x689924,4))[0]
    accepted=key.lower()=='difficulty'
    assert actual==expected and reached==[0x4e8534 if accepted else 0x4e8929]
    return dict(key=key,value=value,difficulty=actual,accepted=accepted)

def random_token(value,previous):
    u=machine();p=0x2010000;u.mem_write(p,value.encode()+b'\0')
    put(u,0x5d8650,'i',previous);put(u,0x6fa2e8,'I',0)
    u.reg_write(UC_X86_REG_EBP,p);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x4e873e,0x4e875a,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x4e875a
    actual=struct.unpack('<i',u.mem_read(0x5d8650,4))[0]
    assert actual==(2 if value.lower()=='random' else previous)
    return dict(value=value,previous=previous,policy=actual)

def verify():
    cases=[difficulty(key,value,expected if key.lower()=='difficulty' else 37)
        for key in ['difficulty','DIFFICULTY','Difficulty','difficultyx','other']
        for value,expected in [('0',0),('1',1),('2',2),('3',3),('-1',-1),('4',4),('101',101),('',0),('invalid',0),('  +2suffix',2)]]
    cases.extend(random_token(value,previous) for value in ['random','RANDOM','Random','randomx','','other'] for previous in [0,1,2])
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Native4e8904 token difficulty dispatch to branch boundaries and4e873e random-token comparison/write; real59db40/59c5a4,no doubles. CRT C-locale path forced6fa2e8=0. Full tokenization/CLI and non-C locale excluded; parsed difficulty not clamped in this slice.')
    (ROOT/'modernization/docs/ai-difficulty-command-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
