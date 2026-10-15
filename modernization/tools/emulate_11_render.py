"""Hash-gated native rasterizer fixture; no terrain captures required."""
import struct,pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX,UC_X86_REG_EIP
import build_remastered_11 as b
class Native:
 def __init__(self):
  engine=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
  assert b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  p=pefile.PE(str(engine));self.u=Uc(UC_ARCH_X86,UC_MODE_32)
  self.u.mem_map(0x400000,0x400000)
  try:self.u.mem_write(0x400000,p.get_memory_mapped_image())
  finally:p.close()
  for address,size in [(0x1400000,0x100000),(0x1800000,0x100000),(0x2000000,0x100000)]:self.u.mem_map(address,size)
 def w(self,address,value):self.u.mem_write(address,struct.pack('<I',value&0xffffffff))
 def call(self,address,args,ecx=0):
  self.u.mem_write(0x20ff000,struct.pack('<'+'I'*(len(args)+1),0x20fe000,*[a&0xffffffff for a in args]))
  self.u.reg_write(UC_X86_REG_ESP,0x20ff000);self.u.reg_write(UC_X86_REG_ECX,ecx)
  self.u.emu_start(address,0x20fe000,count=1000000)
  assert self.u.reg_read(UC_X86_REG_EIP)==0x20fe000
  return self.u.reg_read(UC_X86_REG_EAX)
