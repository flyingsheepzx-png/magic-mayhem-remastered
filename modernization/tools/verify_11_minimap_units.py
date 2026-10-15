"""Execute two actual marker-layout hooks while preserving native row stride."""
import json,struct,pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
import build_11_minimap_units as b

def main():
 p=pefile.PE(str(b.OUT/'qol_bindings.dll'));e=pefile.PE(str(b.base.DEST/'runtime/Chaos-Wide169-engine.exe'));base=p.OPTIONAL_HEADER.ImageBase
 assert b.b.sha(b.base.DEST/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 lines=(b.OUT/'qol_bindings.map').read_text().splitlines()
 def sym(name):return int(next(s for s in lines if '?'+name+'@' in s).split()[2],16)
 checks=0
 for width in [1280,1920,2560]:
  for stride in [1280,2560,4096]:
   for mw,mh in [(80,80),(100,60),(60,100)]:
    for name,site,stop,extent in [('scanner_units_width_a_hook',0x552f29,0x552f4a,mh),('scanner_units_width_b_hook',0x5532f9,0x55331a,mw)]:
     u=Uc(UC_ARCH_X86,UC_MODE_32)
     for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000)]:u.mem_map(a,n)
     u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
     assert bytes(u.mem_read(site,6))==bytes.fromhex('8b86eb000000')
     obj=0x2001000
     for a,v in [(obj+0xeb,stride),(obj+0x103,mw),(obj+0x107,mh),(sym('scanner_layout_width'),width)]:u.mem_write(a,struct.pack('<I',v))
     u.reg_write(UC_X86_REG_ESI,obj);u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EFLAGS,0x246)
     u.emu_start(sym(name),stop,count=100)
     assert struct.unpack('<I',u.mem_read(obj+0xf7,4))[0]==width-extent-8
     assert struct.unpack('<I',u.mem_read(obj+0xfb,4))[0]==6
     assert struct.unpack('<I',u.mem_read(obj+0xeb,4))[0]==stride
     assert u.reg_read(UC_X86_REG_ESP)==0x20ff000;checks+=1
 # Prior inverse/layout/preview recreation suites against the rebuilt module.
 script=(b.b.ROOT/'modernization/tools/verify_11_minimap_release.py').read_text().replace('remastered-1.1-minimap-release','remastered-1.1-minimap-units')
 exec(compile(script,'verify_11_minimap_release.py','exec'),{'__file__':str(b.b.ROOT/'modernization/tools/verify_11_minimap_release.py')})
 v=json.loads((b.OUT/'verification.json').read_text());v.update(result='passed',module_sha256=b.b.sha(b.OUT/'qol_bindings.dll'),unit_layout_cases=checks,save14_verified=False)
 b.b.write(b.OUT/'verification.json',v);print(checks,'marker-layout cases passed')

if __name__=='__main__':main()
