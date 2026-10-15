"""Actual native RLE/anchor plus compiled private upper-layer sprite collector."""
import struct,json,pefile
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import build_11_roof_ghost as b
import os
if os.environ.get('MM_ROOF_VERIFY_V2'):
 import build_11_roof_ghost_v2 as b
OUT=b.OUT
import install_occluded_body
install_occluded_body.installer.BUILD=OUT
source=(b.b.ROOT/'modernization/tools/verify_occluded_units.py').read_text().split('\nchecks=0\n')[0]
source=source.replace('from emulate_terrain_diagonal import Native','from emulate_11_render import Native')
ns={};exec(compile(source,__file__,'exec'),ns)
setup=ns['setup'];run=ns['run'];sym=ns['sym'];p=ns['p'];buffer=ns['buffer'];sprite=ns['sprite']
query=next(x.address for group in p.DIRECTORY_ENTRY_IMPORT for x in group.imports if x.name==b'VirtualQuery')
scene=0x180a000;unit=0x1806000;map_=0x180b000;anim=0x180c000;appearance=0x180d000;table=0x180e000;header=0x180f000;frames=0x1810000;passes=0x1811000;type_=0x1812000
def fixture(rot=0,x=5,y=5):
 n,image=setup();u=n.u
 n.w(0x6e1f0c,1);n.w(0x644520,1);n.w(0x6def58,unit);n.w(0x6def5c,1)
 n.w(0x6c5494,10);n.w(0x6c5498,10);n.w(0x6c54dc,map_)
 for i in range(10):n.w(0x6cb942+i*4,i*10)
 for i in range(32):n.w(0x6cb8c2+i*4,i*100)
 # Scene anchor at the camera's radius-zero cell; its world centre is(176,176).
 for off,v in [(0x11,100),(0x15,100),(0x51,0),(0x55,0),(0x41,0),(0x5d,0),(0x4d,0),(0x45,0),(0x49,0),(0x39,5),(0x3d,5),(0x31,rot),(0x61,1),(0x6d,0)]:n.w(scene+off,v)
 for off,v in [(4,1),(8,x),(12,y),(16,2),(0xe4,100),(0x28,1),(0x14,x*32+16),(0x18,y*32+16),(0x1c,32),(0xb4,anim),(0xcc,appearance),(0xac,type_),(0xcf7,passes),(0xbf3,0),(0xb7b,0),(0xb7f,0)]:n.w(unit+off,v)
 n.w(anim+4,0);n.w(anim+8,1);n.w(anim+12,2);n.w(appearance+0x110,table)
 for j,v in enumerate((header,0,frames,0)):n.w(table+j*4,v)
 n.w(header+12,1);n.w(frames,sprite);n.w(frames+4,sprite)
 for pose in range(30):
  n.w(passes+pose*4,0);n.w(passes+120+pose*4,-1);n.w(passes+240+pose*4,-1)
 n.w(passes+600,0)
 # Large clip isolates projection from culling. Native anchor function executes.
 u.mem_write(sym('clip'),struct.pack('<4i',-1000,-1000,1000,1000))
 u.mem_write(sym('captured'),b'\1');u.mem_write(sym('occluded_units_enabled'),b'\1')
 u.mem_write(sym('body_commands'),b'\0')
 addr=struct.unpack('<I',u.mem_read(query,4))[0];u.mem_map(addr&~4095,4096)
 def trace(u,a,size,data):
  if a==addr:
   sp=u.reg_read(UC_X86_REG_ESP);args=struct.unpack('<4I',u.mem_read(sp,16));ptr=args[2]
   u.mem_write(ptr,struct.pack('<7I',args[1],args[1],4,0x100000,0x1000,4,0x20000))
   u.reg_write(UC_X86_REG_EAX,28);u.reg_write(UC_X86_REG_ESP,sp+16);u.reg_write(UC_X86_REG_EIP,args[0])
 u.hook_add(UC_HOOK_CODE,trace)
 return n
checks=0
for rot,sx,sy in [(0,0,16),(1,32,0),(2,0,-16),(3,-32,0)]:
 n=fixture(rot);before=bytes(n.u.mem_read(unit,0xe4b));scene_before=bytes(n.u.mem_read(scene,0x23d))
 n.call(sym('roof_collect'),[scene]);assert struct.unpack('<I',n.u.mem_read(sym('roof_count'),4))[0]==1
 c=bytes(n.u.mem_read(sym('roof_bodies'),36));assert struct.unpack_from('<3i',c,4)==(sprite,101+sx,70+sy)
 assert bytes(n.u.mem_read(unit,0xe4b))==before and bytes(n.u.mem_read(scene,0x23d))==scene_before
 checks+=1
for address,value in [(unit+0xe4,0),(unit+4,0),(unit+0x28,0),(unit+16,1),(scene+0x6d,1),(scene+0x61,2),(0x6e1f0c,2),(unit+0xb4,0),(passes,1)]:
 n=fixture();n.w(address,value);n.call(sym('roof_collect'),[scene]);assert not struct.unpack('<I',n.u.mem_read(sym('roof_count'),4))[0];checks+=1
for frame in (0,1,2):
 n=fixture();n.w(anim+4,frame);n.call(sym('roof_collect'),[scene]);assert struct.unpack('<I',n.u.mem_read(sym('roof_count'),4))[0]==1;checks+=1
for rot in range(4):
 n=fixture(rot,x=0,y=5);n.w(scene+0x39,9);n.call(sym('roof_collect'),[scene]);c=bytes(n.u.mem_read(sym('roof_bodies'),36))
 sx,sy=[(32,32),(64,-16),(-32,-32),(-64,16)][rot]
 assert struct.unpack_from('<2i',c,8)==(101+sx,70+sy);checks+=1
if os.environ.get('MM_ROOF_VERIFY_V2'):
 for group,selected,airborne,want in [(2,1,0,1),(2,2,0,0),(1,1,0,0),(2,1,1,0),(3,2,0,1)]:
  n=fixture();n.w(scene+0x6d,1);n.w(scene+0x61,28);n.w(scene+0x65,selected);n.w(unit+0x108,airborne)
  n.u.mem_write(map_+(200+50+5)*12+8,bytes([group]))
  n.call(sym('roof_collect'),[scene]);assert struct.unpack('<I',n.u.mem_read(sym('roof_count'),4))[0]==want;checks+=1
 n=fixture();n.u.mem_write(sym('body_commands'),b'\1');n.w(sym('owners'),0)
 n.call(sym('roof_collect'),[scene]);assert not struct.unpack('<I',n.u.mem_read(sym('roof_count'),4))[0];checks+=1
# A ghost absent from the ordinary command list still blends through native RLE.
n,expected=setup();n.w(sym('roof_count'),1);n.w(sym('roof_owners'),0)
n.u.mem_write(sym('roof_bodies'),bytes(n.u.mem_read(sym('saved'),36)))
n.u.mem_write(sym('body_commands'),b'\0')
for y in range(2,6):expected[y][4]=0x6013
assert run(n)==expected;checks+=1
# Visible foreground body wins over ghost; lifecycle/menu exclusion retained.
n,expected=setup();n.w(sym('roof_count'),1);n.w(sym('roof_owners'),0)
n.u.mem_write(sym('roof_bodies'),bytes(n.u.mem_read(sym('saved'),36)))
for y in range(2,6):expected[y][4]=0x6013
assert run(n)==expected;checks+=1
# Existing native rasterizer suite with current37.5% opacity.
test=(b.b.ROOT/'modernization/tools/verify_occluded_units.py').read_text().replace('from emulate_terrain_diagonal import Native','from emulate_11_render import Native').replace('0x780f','0x6013')
exec(compile(test,__file__,'exec'),{'__name__':'__main__'})
other=json.loads((OUT/'occlusion-verification.json').read_text())
b.base.write(OUT/'ghost-verification.json',dict(result='passed',checks=checks+other['checks'],collector_checks=checks,raster_checks=other['checks'],module_sha256=b.b.sha(OUT/'repath.dll'),scope='Compiled ghost collector, actual native camera anchor/RLE rasterizer, four rotations, wrap, upper-layer gates, alive/fog/multiplayer rejection, inclusive animation frames, no scene/unit mutation; VirtualQuery explicit double; runtime bridge acceptance pending'))
print('Passed',checks+other['checks'],'roof ghost/raster checks')
