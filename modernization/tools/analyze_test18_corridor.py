"""Real captured test18 cells with actual native read-only walking validators."""
import json,struct
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
import build_remastered_11 as b
RUN=b.ROOT/'modernization/logs/remastered-ui/test18-path-before-v1'
class Terrain:
 def __init__(self):
  e=b.TARGET/'runtime/Chaos-Wide169-engine.exe';assert b.sha(e)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  self.u=Uc(UC_ARCH_X86,UC_MODE_32);self.u.mem_map(0x400000,0x400000);self.u.mem_write(0x400000,pefile.PE(str(e)).get_memory_mapped_image())
  for a,n in [(0x1000000,0x400000),(0x1400000,0x100000),(0x1800000,0x100000),(0x2000000,0x100000)]:self.u.mem_map(a,n)
  self.u.mem_write(0x1000000,(RUN/'map.bin').read_bytes());self.u.mem_write(0x1400000,(RUN/'tile-types.bin').read_bytes())
  self.unit=0x1801000;self.typ=0x1803000
  self.u.mem_write(self.unit,(RUN/'unit0.bin').read_bytes());self.u.mem_write(self.typ,(RUN/'unit-type.bin').read_bytes());self.w(self.unit+0xac,self.typ)
  w,h,z=json.loads((RUN/'capture.json').read_text())['dimensions']
  for a,v in [(0x6c5494,w),(0x6c5498,h),(0x6c549c,z),(0x6c54a0,w*h),(0x6c54dc,0x1000000),(0x65660c,0x1400000),(0x5e1780,z),(0x6e1f0c,1),(0x6def58,self.unit),(0x6def5c,1)]:self.w(a,v)
  for i in range(h):self.w(0x6cb942+4*i,w*i)
  for i in range(z):self.w(0x6cb8c2+4*i,w*h*i)
 def w(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def call(self,a,args,ecx,budget=200000):
  self.u.mem_write(0x20ff000,struct.pack('<'+'I'*(len(args)+1),0x20fe000,*[v&0xffffffff for v in args]));self.u.reg_write(UC_X86_REG_ESP,0x20ff000);self.u.reg_write(UC_X86_REG_ECX,ecx);self.u.emu_start(a,0x20fe000,count=budget)
  if self.u.reg_read(UC_X86_REG_EIP)!=0x20fe000:raise TimeoutError('Native emulation instruction budget exhausted')
  return self.u.reg_read(UC_X86_REG_EAX)
def main():
 n=Terrain();rows=[]
 for y in range(39,20,-1):
  a=(63,y,9);d=(63,y-1,9)
  clear=n.call(0x4f13f0,[*d,1,4,struct.unpack('<i',n.u.mem_read(n.unit,4))[0]],0x6c5490)
  occupied=n.call(0x522f50,list(d),n.unit)
  n.w(0x1805000,5);edge=n.call(0x514360,[*a,*d,0x1805000,0],n.unit)
  kind=struct.unpack('<i',n.u.mem_read(0x1805000,4))[0]
  rows.append(dict(source=a,target=d,clearance=clear,occupied=occupied,transition=edge,kind=kind))
 print(json.dumps(rows));b.write(RUN/'corridor-analysis.json',rows)
if __name__=='__main__':main()
