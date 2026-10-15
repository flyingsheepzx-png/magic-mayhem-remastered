"""Compiled short-route hook and actual native line generator, offline only."""
import json,struct
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-short-direct'
engine=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
assert b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
e=pefile.PE(str(engine));p=pefile.PE(str(OUT/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
assert e.get_data(0x11292f,7)==bytes.fromhex('8b8c24c4020000')
lines=(OUT/'repath.map').read_text().splitlines()
def sym(name):return int(next(s for s in lines if '?'+name+'@@' in s).split()[2],16)
unit=0x1801000;typ=0x1803000;stack=0x20ff000
def setup(goal=(46,40,5)):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x1800000,0x100000),(0x2000000,0x100000)]:u.mem_map(a,n)
 u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
 def w(a,v):u.mem_write(a,struct.pack('<I',v&0xffffffff))
 for a,v in [(0x6e1f0c,1),(0x6c5494,80),(0x6c5498,80),(0x6c549c,25),(unit+4,1),(unit+0xe4,1),(unit+0x5ec,2),(unit+0xac,typ),(typ+8,1),(typ+12,4),(typ+0x44,1),(unit+8,40),(unit+12,40),(unit+16,5),(unit+0xd03,7)]:w(a,v)
 for i,v in enumerate(goal):w(stack+0x2c0+4*i,v)
 # Stub external terrain response, retain ACTUAL native line generation,
 # direction metadata, loop cap, coordinate wrappers and route construction.
 u.mem_write(0x4f3990,bytes.fromhex('8b442420c70000000000b801000000c22400'))
 u.mem_write(sym('walking_edge'),bytes.fromhex('b001c3'))
 u.mem_write(0x6c4bd0,b'\xa5'*524)
 return u,w
regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
def run(u,success):
 for i,r in enumerate(regs):u.reg_write(r,unit if r==UC_X86_REG_EBP else 0x123400+i)
 u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_EFLAGS,0x246)
 u.emu_start(sym('short_direct_hook'),0x5132ac if success else 0x512936,count=50000)
 assert u.reg_read(UC_X86_REG_ESP)==stack
 assert u.reg_read(UC_X86_REG_EFLAGS)==(0x246 if not success else 0x246)
 for i,r in enumerate(regs):
  expected=unit if r==UC_X86_REG_EBP else 0x123400+i
  if success and r==UC_X86_REG_EDX:expected=0
  if not success and r==UC_X86_REG_ECX:expected=struct.unpack('<I',u.mem_read(stack+0x2c4,4))[0]
  assert u.reg_read(r)==expected
checks=0
for dx,dy in [(6,0),(-6,0),(0,6),(0,-6),(6,6),(-6,-6),(6,-6),(-6,6),(7,3),(-7,-3),(16,0),(1,1)]:
 goal=(40+dx,40+dy,5);u,w=setup(goal);run(u,True)
 route=struct.unpack('<131i',u.mem_read(0x6c4bd0,524));assert route[:3]==goal and route[4]==max(abs(dx),abs(dy))
 points=[route[5+7*i:8+7*i] for i in range(route[4])]
 assert points[-1]==goal
 last=(40,40,5)
 for pos in points:
  assert all(abs(pos[j]-goal[j])<=abs(last[j]-goal[j]) for j in range(3));last=pos
 assert struct.unpack('<I',u.mem_read(unit+0xd03,4))[0]==0
 checks+=1
for a,v,size in [(0x6e1f0c,2,4),(0x6df184,1,4),(unit+4,0,4),(unit+0xe4,0,4),(unit+0x5ec,14,4),(unit+0x618,1,4),(unit+0x104,1,4),(unit+0x10c,1,4),(unit+0x71c,1,1),(unit+0x723,1,1),(typ+8,2,4),(typ+0x44,2,4),(stack+0x2c0,57,4),(stack+0x2c8,6,4),(stack+0x2c0,90,4)]:
 u,w=setup();u.mem_write(a,v.to_bytes(size,'little'));run(u,False);assert bytes(u.mem_read(0x6c4bd0,524))==b'\xa5'*524;checks+=1
for address,code in [(0x4f3990,'31c0c22400'),(sym('walking_edge'),'b000c3')]:
 u,w=setup();u.mem_write(address,bytes.fromhex(code));run(u,False)
 assert bytes(u.mem_read(0x6c4bd0,524))==b'\xa5'*524 and struct.unpack('<I',u.mem_read(unit+0xd03,4))[0]==7;checks+=1
report=dict(result='passed',checks=checks,module_sha256=b.sha(OUT/'repath.dll'),gameplay_tested=False,evidence='Actual native direct line/metadata and compiled hook; external terrain predicates stubbed. Scope, ABI, 16-step cap, failed validation fallback checked. test18 runtime pending.')
b.write(OUT/'verification.json',report);print(report)
