"""Execute native click inverse and compiled adapter across pitch/rotation."""
import hashlib,json,struct
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'modernization/build/remastered-1.1-minimap-center'
engine=ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe'
assert hashlib.sha256(engine.read_bytes()).hexdigest()=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
p=pefile.PE(str(BUILD/'qol_bindings.dll'));e=pefile.PE(str(engine));base=p.OPTIONAL_HEADER.ImageBase
lines=(BUILD/'qol_bindings.map').read_text().splitlines()
def sym(name):return int(next(s for s in lines if '?'+name+'@' in s).split()[2],16)
obj=0x2001000
def click(width,storage,rotation,x,y,patched):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000)]:u.mem_map(a,n)
 u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
 def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
 put(obj+0xeb,storage);put(obj+0xc5,rotation);put(obj+0x6159,0,0,160,80);put(0x6c549c,80)
 put(sym('scanner_layout_width'),width)
 stack=0x20ff000;put(stack,0,1,x,y)
 u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,obj)
 if patched:u.mem_write(0x555f1d,b'\xe9'+struct.pack('<i',sym('scanner_click_width_hook')-0x555f22)+b'\x90')
 u.emu_start(0x555ec0,0x555f6e,count=200)
 assert struct.unpack('<I',u.mem_read(obj+0xeb,4))[0]==storage
 assert u.reg_read(UC_X86_REG_ESP)==stack-0x74
 return tuple(u.reg_read(r) for r in [UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_EFLAGS])
checks=0;detected=0
for width in [1280,1920,2560]:
 for storage in [1280,2560,4096]:
  for rot in range(4):
   for dx,dy in [(80,40),(110,40),(50,40),(80,20),(80,60),(60,30),(100,50)]:
    x=width-168+dx;y=6+dy
    reference=click(width,width,rot,x,y,False)
    assert click(width,storage,rot,x,y,True)==reference
    detected+=int(click(width,storage,rot,x,y,False)!=reference)
    checks+=1
assert detected>0
# Existing compiled scanner layout and sprite/tooltip checks on final module.
path=ROOT/'modernization/tools/verify_11_minimap.py'
source=path.read_text().replace("remastered-1.1-minimap-v2'","remastered-1.1-minimap-center'")
exec(compile(source,str(path),'exec'),{'__file__':str(path)})
report=dict(result='passed',click_checks=checks,old_mismatch_cases=detected,qol_sha256=hashlib.sha256((BUILD/'qol_bindings.dll').read_bytes()).hexdigest(),scope='compiled adapter + native inverse for 4 rotations, 3 logical widths, 3 storage widths; unchanged storage and stack; existing scanner/UI tests passed')
(BUILD/'center-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
