"""Compiled wait hooks on the real save14 dynamic obstacle and prior routes."""
import struct,json,pefile
import analyze_test18_corridor as a
import build_11_dynamic_wait as b
from unicorn.x86_const import *
P=pefile.PE(str(b.OUT/'repath.dll'));BASE=P.OPTIONAL_HEADER.ImageBase
LINES=(b.OUT/'repath.map').read_text().splitlines()
def sym(name):return int(next(x for x in LINES if '?'+name+'@@' in x).split()[2],16)
def setup():
 a.RUN=b.b.ROOT/'modernization/logs/remastered-ui/save14-route-before-v1/blocked'
 n=a.Terrain();n.u.mem_map(BASE,(P.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(BASE,P.get_memory_mapped_image());return n
def ints(n,off,count=1):return struct.unpack('<'+'i'*count,n.u.mem_read(n.unit+off,count*4))
REGS=(UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP)
def hook(n,name,end):
 for k,r in enumerate(REGS):n.u.reg_write(r,n.unit if r==UC_X86_REG_ESI else 0x123400+k)
 n.u.reg_write(UC_X86_REG_ESP,0x20ff000);n.u.reg_write(UC_X86_REG_EFLAGS,0x246)
 n.u.emu_start(sym(name),end,count=10000000)
 assert n.u.reg_read(UC_X86_REG_EIP)==end and n.u.reg_read(UC_X86_REG_ESP)==0x20ff000
 assert n.u.reg_read(UC_X86_REG_EFLAGS)==0x246
 for k,r in enumerate(REGS):
  expect=n.unit if r==UC_X86_REG_ESI else 0x123400+k
  if name=='wait_tick_hook' and r==UC_X86_REG_EAX:expect=ints(n,0x66c)[0]
  assert n.u.reg_read(r)==expect
def arm(n):hook(n,'blocked_wait_hook',0x511be7)
def tick(n):hook(n,'wait_tick_hook',0x50f829)
def main():
 checks=0;n=setup();arm(n);tick(n);assert ints(n,0x66c)==(7,);checks+=1
 n=setup();hook(n,'dynamic_blocked_wait_hook',0x5112c3);assert ints(n,0x66c)==(5,)
 tick(n);assert ints(n,0x66c)==(1,) and ints(n,0x96b,5)==(18,53,6,0,7);checks+=1
 n=setup();arm(n)
 n.w(n.unit+0x66c,6);old=n.u.mem_read(n.unit,0xe4b);cells=n.u.mem_read(0x1000000,12*80*80*30);tick(n)
 route=ints(n,0x96b,131);path=[route[5+i*7:8+i*7] for i in range(route[4])]
 assert route[:5]==(18,53,6,0,7) and path[0]==(17,47,6) and path[-1]==(18,53,6) and (18,47,6) not in path
 assert ints(n,0x66c)==(1,) and ints(n,0xd03)==(0,)
 new=n.u.mem_read(n.unit,0xe4b)
 allowed=set(range(0x96b,0x96b+524))|set(range(0x66c,0x670))|set(range(0xd03,0xd07))
 assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(old,new)))
 assert n.u.mem_read(0x1000000,len(cells))==cells;checks+=3
 # An ordinary unit occupancy wait must not be rerouted by this fire policy.
 n=setup();arm(n);cell=0x1000000+12*(18+80*47+6400*6)
 n.u.mem_write(cell+4,struct.pack('<H',2));n.u.mem_write(cell+10,struct.pack('<H',1));n.w(n.unit+0x66c,6)
 old=n.u.mem_read(n.unit+0x96b,524);tick(n);assert ints(n,0x66c)==(6,) and n.u.mem_read(n.unit+0x96b,524)==old;checks+=1
 # Cleared fire still wakes immediately, preserving the original route.
 n=setup();arm(n);n.u.mem_write(cell+10,b'\0\0');n.w(n.unit+0x66c,6);old=n.u.mem_read(n.unit+0x96b,524)
 tick(n);assert ints(n,0x66c)==(1,) and n.u.mem_read(n.unit+0x96b,524)==old;checks+=1
 # Fully blocked goal has no detour; route/timer and occupancy remain native.
 n=setup();arm(n);goal=0x1000000+12*(18+80*53+6400*6);n.u.mem_write(goal+10,struct.pack('<H',0x10));n.w(n.unit+0x66c,6)
 old=n.u.mem_read(n.unit+0x96b,524);tick(n);assert ints(n,0x66c)==(6,) and n.u.mem_read(n.unit+0x96b,524)==old;checks+=1
 # Cooldown survives consecutive wait cycles. Make a detour possible again;
 # it remains suppressed until enough native waiting updates have elapsed.
 n.u.mem_write(goal+10,b'\0\0');arm(n);n.w(n.unit+0x66c,6);tick(n);assert ints(n,0x66c)==(6,);checks+=1
 for _ in range(6):
  arm(n)
  for timer in range(7,1,-1):
   n.w(n.unit+0x66c,timer);tick(n)
   if ints(n,0x66c)==(1,):break
  if ints(n,0x66c)==(1,):break
 assert ints(n,0x66c)==(1,);checks+=1
 for off,value,size in [(0x6e1f0c,2,4),(0x1801000+4,0,4),(0x1801000+0xe4,0,4),(0x1801000+0x5ec,14,4),(0x1801000+0x5fc,2,4),(0x1801000+0x618,1,4),(0x1801000+0x104,1,4),(0x1801000+0x10c,1,4),(0x1801000+0x71c,1,1),(0x1801000+0x723,1,1),(0x1803000+8,2,4),(0x1803000+0x44,2,4),(0x1801000,2,4),(0x1801000+8,17,4),(0x1801000+0x96b,19,4),(0x1801000+0x977,3,4),(0x1801000+0x97b,17,4)]:
  n=setup();arm(n);n.u.mem_write(off,value.to_bytes(size,'little'));n.w(n.unit+0x66c,6);old=n.u.mem_read(n.unit,0xe4b);tick(n);assert n.u.mem_read(n.unit,0xe4b)==old;checks+=1
 for name,end in [('reset_hook',0x5060a7),('deserialize_hook',0x527316)]:
  n=setup();arm(n);n.u.reg_write(UC_X86_REG_ECX,n.unit);n.u.reg_write(UC_X86_REG_ESP,0x20ff000);n.u.emu_start(sym(name),end,count=1000000)
  n.w(n.unit+0x66c,6);old=n.u.mem_read(n.unit,0xe4b);tick(n);assert n.u.mem_read(n.unit,0xe4b)==old;checks+=1
 # Execute existing save3 local route/test18 corridor suite against new module.
 import build_11_local_route as prior
 prior.OUT=b.OUT
 import verify_save3_local_route as regression
 regression.main();checks+=8
 fixture=b.b.ROOT/'modernization/logs/remastered-ui/save14-route-before-v1/blocked/capture.json'
 b.base.write(b.OUT/'verification.json',dict(result='passed',checks=checks,module_sha256=b.b.sha(b.OUT/'repath.dll'),path=path,fixture_sha256=json.loads(fixture.read_text())['fixture_sha256'],native_validators=True,save14_runtime_verified=False))
 print('passed',checks,path)
if __name__=='__main__':main()
