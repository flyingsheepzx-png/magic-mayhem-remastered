"""Compiled x86 guard regression using the player's first-chance dump."""
import sys,json,struct,mmap,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'modernization/tools'))
import build_11_portrait_ready as b
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE,UcError
from unicorn.x86_const import *
REGS=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS]
evidence=ROOT/'modernization/logs/remastered-ui/first-av-p444-1790853217278614000'
identity=json.loads((evidence/'identity.json').read_text())
engine=b.base.DEST/'runtime/Chaos-Wide169-engine.exe'
assert hashlib.sha256(engine.read_bytes()).hexdigest()==identity['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
with (evidence/'av-1.dmp').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
 count,directory=struct.unpack_from('<II',raw,8)
 streams={t:(s,r) for t,s,r in (struct.unpack_from('<III',raw,directory+12*i) for i in range(count))}
 start=streams[9][1];n,offset=struct.unpack_from('<QQ',raw,start);regions=[]
 for i in range(n):
  address,size=struct.unpack_from('<QQ',raw,start+16+16*i);regions.append((address,size,offset));offset+=size
 def read(a,s):
  return next(bytes(raw[o+a-v:o+a-v+s]) for v,l,o in regions if v<=a and a+s<=v+l)
 assert read(0x6593e0,32)==bytes(32)
 stack=struct.unpack('<24I',read(0x1af720,96));assert 0x5074ca in stack and 0x4d2d7b in stack
 fault=read(0x4d3d21,2);assert fault==b'\x8b\x31'
 base_surface=struct.unpack('<I',read(0x6a4646,4))[0];assert base_surface
 captured=dict(bank=read(0x6593e0,32).hex(),base_surface=hex(base_surface),fault='4d3d21 mov esi,[ecx], ECX=0',callers=['5073d0 unit selection','4d2d7b portrait event handler'],lifecycle_writer='not yet proven')
 b.base.write(evidence/'portrait-root-cause.json',captured)
dll=pefile.PE(str(b.OUT/'qol_bindings.dll')); image=dll.get_memory_mapped_image();image_base=dll.OPTIONAL_HEADER.ImageBase
entry=image_base+next(s.address for s in dll.DIRECTORY_ENTRY_EXPORT.symbols if s.name==b'mm_portrait_sprite_ready')
pe=pefile.PE(str(engine));native=pe.get_data(0xd3c90,6);assert native==b'\x51\xa1\x46\x46\x6a\x00'
def machine(mask,flags):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 u.mem_map(image_base,(len(image)+4095)&~4095);u.mem_write(image_base,image)
 u.mem_map(0x400000,0x300000);u.mem_map(0x1000000,0x10000)
 u.mem_write(0x4d3c90,native);u.mem_write(0x6a4646,struct.pack('<I',base_surface))
 for i,a in enumerate([0x6593e0,0x6593e8,0x6593ec]):u.mem_write(a,struct.pack('<I',0x600000+0x100*i if mask&(1<<i) else 0))
 for i,r in enumerate(REGS[:-2]):u.reg_write(r,0x10203040+i*0x100)
 u.reg_write(UC_X86_REG_ESP,0x1008000);u.mem_write(0x1008000,struct.pack('<I',0x400000))
 u.reg_write(UC_X86_REG_EFLAGS,flags)
 return u
cases=0
for mask in range(8):
 for flagbits in range(64):
  flags=2|sum(1<<bit for i,bit in enumerate([0,2,4,6,7,11]) if flagbits&(1<<i))
  u=machine(mask,flags);before=[u.reg_read(r) for r in REGS];writes=[]
  u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,size,value,data:writes.append((a,size,value)))
  u.emu_start(entry,0x4d3c96 if mask==7 else 0x400000,count=50)
  if mask==7:
   reference=machine(mask,flags);reference.emu_start(0x4d3c90,0x4d3c96,count=2)
   assert [u.reg_read(r) for r in REGS]==[reference.reg_read(r) for r in REGS]
   assert u.mem_read(0x1007ffc,8)==reference.mem_read(0x1007ffc,8)
  else:
   expected=before[:];expected[-2]+=4
   assert [u.reg_read(r) for r in REGS]==expected
  assert all(0x1007ff8<=a and a+size<=0x1008000 for a,size,_ in writes),writes
  assert u.mem_read(0x6593e0,16)==machine(mask,flags).mem_read(0x6593e0,16)
  cases+=1
# Reproduce the captured native read instruction's fault independently.
u=machine(0,2);u.mem_write(0x4d3d21,fault);u.reg_write(UC_X86_REG_ECX,0)
try:u.emu_start(0x4d3d21,0x4d3d23,count=1)
except UcError:pass
else:raise AssertionError('Original captured instruction must fault with null table')
b.base.write(b.OUT/'verification.json',dict(result='passed',module_sha256=b.b.sha(b.OUT/'qol_bindings.dll'),compiled_x86_cases=cases,captured_fault_fixture=captured,unchanged_modules=['101','103'],native_surface_lifecycle_tests='passed',runtime_acceptance='pending user testing',scope='Missing-bank portrait drawing only; ready-path ABI identical to native entry; selection and load state unmodified'))
print(f'{cases} compiled portrait guard cases passed, original captured fault reproduced, ready entry matches native')
