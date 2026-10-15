"""Execute compiled detours with OS/settings boundaries stubbed only."""
import sys,re,struct,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'modernization/tools'))
import prepare_options_window as b
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
out=b.OUT;pe=pefile.PE(str(out/'qol_bindings.dll'));image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
mapping=(out/'qol_bindings.map').read_text()
def symbol(name):
 rows=[line for line in mapping.splitlines() if '?'+name+'@' in line]
 assert len(rows)==1,(name,rows)
 return int(re.search(r'\s([0-9a-fA-F]{8})\s+f',rows[0])[1],16)
setup=symbol('window_setup');apply=symbol('window_apply');load=symbol('selected_window_mode');select=symbol('select_window_mode')
registers=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS]
count=0
for high in [0,1]:
 for flag in range(64):
  for entry,end in [(setup,0x4a9512),(apply,0x4a9949)]:
   u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,image);u.mem_map(0x400000,0x300000);u.mem_map(0x1000000,0x10000)
   for i,r in enumerate(registers[:-2]):u.reg_write(r,0x102000+i*256)
   u.reg_write(UC_X86_REG_EAX,high);u.reg_write(UC_X86_REG_ECX,high);u.reg_write(UC_X86_REG_ESP,0x1008000)
   flags=2|sum(1<<bit for i,bit in enumerate([0,2,4,6,7,11]) if flag&(1<<i));u.reg_write(UC_X86_REG_EFLAGS,flags)
   u.mem_write(0x6de6f1,struct.pack('<I',1));before=[u.reg_read(r) for r in registers];calls=[]
   def boundary(uc,a,size,data):
    if a not in [load,select]:return
    sp=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
    if a==select:calls.append(struct.unpack('<I',uc.mem_read(sp+4,4))[0])
    uc.reg_write(UC_X86_REG_EAX,high);uc.reg_write(UC_X86_REG_ECX,0xbad);uc.reg_write(UC_X86_REG_EDX,0xbad)
    uc.reg_write(UC_X86_REG_ESP,sp+4);uc.reg_write(UC_X86_REG_EIP,ret)
   u.hook_add(UC_HOOK_CODE,boundary);u.emu_start(entry,end,count=80)
   expected=before[:]
   if entry==setup:expected[3]=high
   assert [u.reg_read(r) for r in registers]==expected
   assert u.mem_read(0x6de6f1,4)==struct.pack('<I',1)
   assert calls==([high] if entry==apply else [])
   count+=1

print(count,"compiled window-mode detour cases passed")
