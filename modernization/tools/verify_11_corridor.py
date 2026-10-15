"""Actual compiled/native path checks on captured test18 geometry, no stubs."""
import struct,pefile
from unicorn.x86_const import *
from analyze_test18_corridor import Terrain
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-corridor'
p=pefile.PE(str(OUT/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(OUT/'repath.map').read_text().splitlines()
def sym(name):return int(next(x for x in lines if '?'+name+'@@' in x).split()[2],16)
def setup():
 n=Terrain();n.u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(base,p.get_memory_mapped_image());return n
def route(n,g=(63,20,9)):
 n.u.mem_write(0x1806000,b'\xa5'*524)
 result=n.call(sym('corridor_route'),[n.unit,*g,0x1806000],0)&255
 return result,struct.unpack('<131i',n.u.mem_read(0x1806000,524))
n=setup();yes,r=route(n);assert yes==1 and r[:5]==(63,20,9,0,16)
assert all(r[5+i*7]==63 for i in range(16))
assert [r[7+i*7] for i in range(16)]==[9,9,10,11,12,13,13,13,13,12,11,10,9,9,9,9]
checks=1
# Block a corridor cell: actual native collision rejects, output untouched.
n=setup()
for z in range(9,18):n.u.mem_write(0x1000000+12*(63+35*100+z*10000)+10,struct.pack('<H',0x4000))
yes,r=route(n);assert not yes and bytes(n.u.mem_read(0x1806000,524))==b'\xa5'*524;checks+=1
for off,value in [(0x6e1f0c,2),(0x1801000+0x5ec,14),(0x1803000+8,2),(0x1803000+0x44,2),(0x1801000+0x10c,1)]:
 n=setup();n.w(off,value);assert route(n)[0]==0;checks+=1
n=setup();assert route(n,(63,20,8))[0]==0;checks+=1
# The deserialize adapter marks the original ECX unit, despite caller-clobber.
n=setup();u=n.u
u.mem_write(sym('on_unit_replaced'),bytes.fromhex('b9efbeadde c3'))
stack=0x20ff000;u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,n.unit);u.reg_write(UC_X86_REG_EFLAGS,0x246)
u.emu_start(sym('deserialize_hook'),0x527316,count=10000)
assert u.reg_read(UC_X86_REG_ECX)==n.unit and u.reg_read(UC_X86_REG_ESP)==stack-0x148
assert u.mem_read(sym('loaded_route_pending'),1)==b'\x01';checks+=1
report=dict(result='passed',checks=checks,module_sha256=b.sha(OUT/'repath.dll'),native_terrain=True,fixture_sha256=b.sha(b.TARGET/'runtime/Save/test18.sav'),scope='Actual native transitions, occupancy, direct generator and compiled corridor on captured test18; ramp heights, solid fallback, scope and deserialize ABI.')
b.write(OUT/'verification.json',report);print(report)
