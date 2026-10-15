"""Execute scanner adapters and original layout arithmetic on verified x86."""
import hashlib,json,struct,runpy
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'modernization/build/remastered-1.1-minimap-v2'
engine=ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe'
assert hashlib.sha256(engine.read_bytes()).hexdigest()=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
p=pefile.PE(str(BUILD/'qol_bindings.dll'));e=pefile.PE(str(engine));base=p.OPTIONAL_HEADER.ImageBase
lines=(BUILD/'qol_bindings.map').read_text(encoding='utf-8').splitlines()
def sym(name):return int(next(s for s in lines if '?'+name+'@' in s).split()[2],16)
checks=0
for width in [1280,1920,2560]:
 for pitch in [2560,5120,8192]:
  for mw,mh in [(80,80),(100,60),(60,100)]:
   u=Uc(UC_ARCH_X86,UC_MODE_32)
   for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000)]:u.mem_map(a,n)
   u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
   def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
   obj=0x2001000;put(obj+0xca,pitch//2);put(obj+0xe2,mw);put(obj+0x613c,6);put(sym('scanner_layout_width'),width)
   u.reg_write(UC_X86_REG_ESI,obj);u.reg_write(UC_X86_REG_ECX,mw);u.reg_write(UC_X86_REG_EDX,mh);u.reg_write(UC_X86_REG_EBP,mw)
   u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EFLAGS,0x246)
   u.emu_start(sym('scanner_width_hook'),0x554b35,count=200)
   assert struct.unpack('<4I',u.mem_read(obj+0x6138,16))==(width-8-mw-mh,6,width-8,6+(mw+mh)//2)
   assert struct.unpack('<I',u.mem_read(obj+0xca,4))[0]==pitch//2
   u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EFLAGS,0x246)
   u.emu_start(sym('scanner_draw_width_hook'),0x554919,count=200)
   assert u.reg_read(UC_X86_REG_EAX)==width-mw-8
   assert u.reg_read(UC_X86_REG_ESP)==0x20ff000
   u.emu_start(sym('scanner_refresh_width_hook'),0x555ba1,count=200)
   assert struct.unpack('<I',u.mem_read(obj+0xd6,4))[0]==width-mw-8
   assert struct.unpack('<I',u.mem_read(obj+0xca,4))[0]==pitch//2
   checks+=1
# Existing tooltip and all-state sprite tests must still pass on this module.
source=(ROOT/'modernization/tools/verify_11_ui_elements.py').read_text(encoding='utf-8')
exec(compile(source.replace("remastered-1.1-ui-elements'","remastered-1.1-minimap-v2'"),str(ROOT/'modernization/tools/verify_11_ui_elements.py'),'exec'),{'__file__':str(ROOT/'modernization/tools/verify_11_ui_elements.py')})
report=dict(result='passed',scanner_checks=checks,qol_sha256=hashlib.sha256((BUILD/'qol_bindings.dll').read_bytes()).hexdigest(),engine_sha256=hashlib.sha256(engine.read_bytes()).hexdigest(),scope='actual compiled adapters + native rectangle/draw arithmetic; primary stride preserved')
(BUILD/'minimap-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report)
