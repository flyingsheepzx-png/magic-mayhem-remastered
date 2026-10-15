"""Execute real native WndProc + compiled close adapter with Win32 stubs."""
import struct
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-window-close'
engine=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
assert b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
e=pefile.PE(str(engine));p=pefile.PE(str(OUT/'qol_bindings.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(OUT/'qol_bindings.map').read_text().splitlines()
target=int(next(x for x in lines if '?alt_f4_close@' in x).split()[2],16)
def setup(patched,alt=True):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000),(0x3000000,0x10000)]:u.mem_map(a,n)
 u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
 def w(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
 assert u.mem_read(0x5c4271,7)==bytes.fromhex('6a00e89834fdff')
 assert u.mem_read(0x5c4294,8)==bytes.fromhex('817c2414a1000000')
 if patched:
  u.mem_write(0x5c4271,b'\xe9'+struct.pack('<i',target-0x5c4276)+b'\x90'*2)
  u.mem_write(0x5c4294,b'\xe9'+struct.pack('<i',0x5c42b1-0x5c4299)+b'\x90'*3)
 stubs=[(0x5c5290,0x3000000,1,0x8000 if alt else 0),(0x5c5270,0x3000100,4,1),(0x5c525c,0x3000200,1,0),(0x5c528c,0x3000300,2,0),(0x5c5268,0x3000400,4,42)]
 for iat,a,argc,r in stubs:w(iat,a);u.mem_write(a,b'\xb8'+struct.pack('<I',r)+b'\xc2'+struct.pack('<H',argc*4))
 records=[]
 def trace(u,a,size,data):
  if a in [s[1] for s in stubs]:
   argc=next(s[2] for s in stubs if s[1]==a);sp=u.reg_read(UC_X86_REG_ESP)
   records.append((hex(a),list(struct.unpack('<'+'I'*argc,u.mem_read(sp+4,argc*4)))))
 u.hook_add(UC_HOOK_CODE,trace,begin=0x3000000,end=0x3000400)
 return u,w,records
checks=0
for patched in [False,True]:
 for hwnd in [0x1111,0xabcde]:
  u,w,events=setup(patched);stack=0x20ff000;w(stack,0x20fe000,hwnd,0x104,0x73,0x203e0001)
  keep=[UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
  for i,r in enumerate(keep):u.reg_write(r,0x123400+i)
  u.reg_write(UC_X86_REG_ESP,stack);u.emu_start(0x4e9d60,0x20fe000,count=2000)
  assert u.reg_read(UC_X86_REG_ESP)==stack+20
  assert all(u.reg_read(r)==0x123400+i for i,r in enumerate(keep))
  if patched:assert events==[('0x3000000',[0x12]),('0x3000100',[hwnd,0x10,0,0])]
  else:assert events==[('0x3000000',[0x12]),('0x3000200',[0])]
  checks+=1
for key,alt in [(0x73,False),(0x72,True),(0x0d,True)]:
 states=[]
 for patched in [False,True]:
  u,w,events=setup(patched,alt);w(0x20ff000,0x20fe000,0x1111,0x104,key,0x203e0001)
  u.reg_write(UC_X86_REG_ESP,0x20ff000);u.emu_start(0x4e9d60,0x20fe000,count=2000);states.append(events)
 assert states[0]==states[1];checks+=1
# WM_CLOSE still follows original DefWindowProc; WM_DESTROY enters cleanup.
u,w,events=setup(True);w(0x20ff000,0x20fe000,0x1111,0x10,0,0);u.reg_write(UC_X86_REG_ESP,0x20ff000)
u.emu_start(0x4e9d60,0x20fe000,count=2000);assert events==[('0x3000400',[0x1111,0x10,0,0])];checks+=1
u,w,events=setup(True);w(0x20ff000,0x20fe000,0x1111,2,0,0);u.reg_write(UC_X86_REG_ESP,0x20ff000)
u.emu_start(0x4e9d60,0x4e9dd6,count=2000);checks+=1
# Title close shortcut now dispatches its original message, including arbitrary
# other messages, with identical stack and exact original MSG pointer.
for msg,hit in [(0xa1,20),(0xa1,2),(0x100,0x41)]:
 u,w,events=setup(True);w(0x20ff000+0x10,0x1111,msg,hit,0);u.reg_write(UC_X86_REG_ESP,0x20ff000)
 u.emu_start(0x5c4294,0x5573de,count=50);assert u.reg_read(UC_X86_REG_ESP)==0x20feffc
 assert struct.unpack('<I',u.mem_read(0x20feffc,4))[0]==0x20ff010;assert not events;checks+=1
report=dict(result='passed',checks=checks,module_sha256=b.sha(OUT/'qol_bindings.dll'),scope='Native window procedure plus compiled Alt+F4 adapter: WM_CLOSE queued, no early WM_QUIT, callee registers/stack, other system keys, native close/destroy branches and title-message dispatch. Win32 APIs stubbed; actual exit acceptance pending user.')
b.write(OUT/'verification.json',report);print(report)
