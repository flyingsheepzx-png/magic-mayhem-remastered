"""Whole native4644d0 version5 loader with in-memory read-only IO doubles."""
import hashlib,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from inspect_ai_animation_assets import RUNTIME

def fixture(path,reloads,fault=None):
    original=path.read_bytes();raw=original;enabled=[False]
    if fault=='size':raw=raw[:4]+struct.pack('<I',len(raw)+1)+raw[8:]
    u=machine();bank=0x2010000;name=bank+0x400
    u.mem_write(name,path.name.encode()+b'\0');position=[0];opens=[];closed=[];allocations={};freed=set();bump=[0x2200000];reads=[]
    entries=(0x4a1120,0x597880,0x5979b0,0x59c359,0x59c4c3,0x5b74d8,0x59d9eb)
    for entry in entries:u.mem_write(entry,b'\xc3')
    def inspect(uc,address,size,user):
        if address not in entries:return
        sp=uc.reg_read(UC_X86_REG_ESP)
        if address==0x4a1120:
            assert uc.reg_read(UC_X86_REG_ECX)==name;position[0]=0;opens.append(1);uc.reg_write(UC_X86_REG_EAX,0 if enabled[0] and fault=='open' else 77)
        elif address==0x597880:
            n=word(uc,sp+4);p=bump[0];bump[0]+=(n+15)&~15;assert bump[0]<0x23d0000
            allocations[p]=n;uc.reg_write(UC_X86_REG_EAX,p)
        elif address==0x5979b0:
            p=word(uc,sp+4);assert p in allocations and p not in freed;freed.add(p)
        elif address==0x59c359:
            out,unit,count,handle=struct.unpack('<4I',uc.mem_read(sp+4,16));assert handle==77
            length=unit*count;data=(raw if enabled[0] else original)[position[0]:position[0]+length];assert len(data)==length
            stage='header' if position[0]==0 else 'index' if position[0]==44 else 'records'
            if enabled[0] and fault==stage:data=data[:-1]
            if data:uc.mem_write(out,data)
            position[0]+=len(data);reads.append(len(data));uc.reg_write(UC_X86_REG_EAX,len(data)//unit)
        elif address==0x59c4c3:
            assert word(uc,sp+4)==77;closed.append(1);uc.reg_write(UC_X86_REG_EAX,0)
        elif address==0x5b74d8:uc.reg_write(UC_X86_REG_EAX,88)
        elif address==0x59d9eb:
            assert word(uc,sp+4)==88;uc.reg_write(UC_X86_REG_EAX,len(raw))
    u.hook_add(UC_HOOK_CODE,inspect)
    count=struct.unpack_from('<I',raw,20)[0];offset=44+count*4
    for _ in range(reloads):
        assert call(u,0x4644d0,bank,[name,0])==1
        assert position[0]==len(raw)
        assert bytes(u.mem_read(word(u,bank),44))==original[:44]
        assert bytes(u.mem_read(word(u,bank+4),count*4))==raw[44:offset]
        assert bytes(u.mem_read(word(u,bank+8),len(raw)-offset))==raw[offset:]
        assert set(allocations)-freed=={word(u,bank),word(u,bank+4),word(u,bank+8)}
    assert len(opens)==len(closed)==reloads
    residual=None
    if fault:
        old=set(allocations)-freed;enabled[0]=True
        assert call(u,0x4644d0,bank,[name,0])==0
        assert old<=freed
        assert len(opens)==reloads+1 and len(closed)==reloads+int(fault!='open')
        pointers=[word(u,bank+o) for o in (0,4,8)]
        residual={hex(p):allocations[p] for p in set(allocations)-freed}
        assert set(allocations)-freed=={p for p in pointers if p}
        expected_count={'open':0,'header':1,'index':2,'records':3,'size':3}[fault]
        assert len(residual)==expected_count
    call(u,0x464480,bank,[])
    assert freed==set(allocations) and all(word(u,bank+o)==0 for o in (0,4,8))
    call(u,0x464480,bank,[])
    assert freed==set(allocations)
    assert path.read_bytes()==original
    return dict(path=str(path),sha256=hashlib.sha256(original).hexdigest(),reloads=reloads,fault=fault,allocations=len(allocations),freed=len(freed),read_lengths=reads,residual_bank_allocations_before_cleanup=residual,native_cleanup_twice=True,record_bytes_unchanged=not fault)

def verify():
    paths=sorted(p for p in (RUNTIME/'Sprites').glob('*') if p.suffix.lower()=='.ani' and p.stem.lower().startswith('effects'))
    cases=[fixture(path,reloads) for path in paths for reloads in (1,2)]
    cases.extend(fixture(path,reloads,fault) for path in paths for reloads in (0,1) for fault in ('open','header','index','records','size'))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole4644d0 native version5 loader:26 success/reload and130 open/short-header/index/records/size failure fixtures on13 installed ANI files,first load or after good load. IO/CRT explicit doubles; native processing unchanged. Failure returns0,old buffers freed,partial new buffers remain bank-owned,opened handles closed. Actual464480 cleanup twice after each fixture frees all exactly once and nulls pointers. Bank+0c=0 excludes sprite load. Allocator failure,versions1..4,sprite association/OS IO and production caller failure cleanup dispatch pending; source files unchanged.')
    (ROOT/'modernization/docs/ai-animation-loader-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
