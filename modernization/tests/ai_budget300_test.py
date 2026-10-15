"""Compiled production detours + real native split, no game launch or file IO."""
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import pefile
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'modernization/tools'))
from verify_ai_training_math import machine,put
from verify_ai_model_native import SHA

OUT=ROOT/'modernization/build/remastered-1.1-ai-budget300'
pe=pefile.PE(str(OUT/'qol_bindings.dll'))
image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
exports={s.name.decode().lstrip('_'):base+s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
cases=0
for site,name,stop in [(0x46b5be,'mm_ai_budget_a_hook',0x46b5c3),(0x46b5d3,'mm_ai_budget_b_hook',0x46b5d8)]:
    for mode,timesystem,total,flags in itertools.product((0,1,2), (0,1,2), (0,30,120,300), (0x202,0x246,0x603)):
        u=machine();u.mem_map(base,(len(image)+0xfff)&~0xfff);u.mem_write(base,image)
        put(u,0x6e1f0c,'I',mode);put(u,0x6e1f64,'I',timesystem);put(u,0x5e15f4,'I',total)
        regs={UC_X86_REG_EBX:0x234567,UC_X86_REG_ECX:0x6789ab,UC_X86_REG_EDX:0x13579,
              UC_X86_REG_ESI:0xabcdef,UC_X86_REG_EDI:0x876543,UC_X86_REG_EBP:0x2030000,
              UC_X86_REG_ESP:0x23f0000,UC_X86_REG_EFLAGS:flags}
        for reg,value in regs.items():u.reg_write(reg,value)
        u.emu_start(exports[name],stop,count=100)
        assert u.reg_read(UC_X86_REG_EIP)==stop
        assert u.reg_read(UC_X86_REG_EAX)==(300 if mode==0 and timesystem==0 else total)
        for reg,value in regs.items():assert u.reg_read(reg)==value,(reg,value,u.reg_read(reg))
        cases+=1

integrations=0
for mode,timesystem,total in itertools.product((0,1,2),(0,1,2),(30,120,300)):
    u=machine();u.mem_map(base,(len(image)+0xfff)&~0xfff);u.mem_write(base,image)
    put(u,0x6e1f0c,'I',mode);put(u,0x6e1f64,'I',timesystem);put(u,0x5e15f4,'I',total)
    for site,name in [(0x46b5be,'mm_ai_budget_a_hook'),(0x46b5d3,'mm_ai_budget_b_hook')]:
        assert bytes(u.mem_read(site,5))==b'\xa1\xf4\x15\x5e\0'
        u.mem_write(site,b'\xe9'+struct.pack('<i',exports[name]-site-5))
    captured=[]
    def scheduler(uc,address,size,_):
        if address!=0x415c40:return
        esp=uc.reg_read(UC_X86_REG_ESP)
        ret,allowance=struct.unpack('<II',uc.mem_read(esp,8))
        captured.append((uc.reg_read(UC_X86_REG_ECX),allowance))
        uc.reg_write(UC_X86_REG_ESP,esp+8);uc.reg_write(UC_X86_REG_EIP,ret)
    u.hook_add(UC_HOOK_CODE,scheduler);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x46b5be,0x46b5e8,count=200)
    allowance=(300 if mode==0 and timesystem==0 else total)//2
    assert captured==[(0x690600,allowance),(0x644550,allowance)]
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0000
    u.reg_write(UC_X86_REG_EBX,allowance);u.reg_write(UC_X86_REG_EBP,0x2030000)
    u.emu_start(0x415ca0,0x415cad,count=20)
    assert u.reg_read(UC_X86_REG_EDI)==allowance//2
    u.reg_write(UC_X86_REG_EBX,allowance)
    u.emu_start(0x416384,0x416386,count=5)
    assert u.reg_read(UC_X86_REG_EBX)==allowance-allowance//2
    assert struct.unpack('<I',u.mem_read(0x5e15f4,4))[0]==total
    integrations+=1

report=dict(result='passed',engine_sha256=SHA,module_sha256=hashlib.sha256((OUT/'qol_bindings.dll').read_bytes()).hexdigest(),
            compiled_hook_cases=cases,native_caller_integrations=integrations,
            singleplayer_total=300,scheduler_allowance=150,planning_each=75,execution_each=75,
            mode_guard='6e1f0c==0 and NOTIONAL6e1f64==0 only; multiplayer and REAL_TIME retain native config',
            unchanged_modules=[101,103],native_surface_lifecycle_tests='passed during build',
            runtime_acceptance='pending user testing; no gameplay launched',
            scope='Compiled detours preserve flags/non-EAX registers/stack; real disk normal caller and split slices; scheduler entry explicitly doubled. Config global unmodified; startup unlimited branch unmodified.')
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
