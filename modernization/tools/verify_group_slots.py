import sys,struct
sys.path.insert(0,'modernization/tools')
from emulate_terrain_diagonal import Native
from install_group_slots import installer as i
import pefile
from unicorn.x86_const import *
p=pefile.PE(str(i.BUILD/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
hook=int(next(x for x in (i.BUILD/'repath.map').read_text().splitlines() if '?group_slot_hook@@' in x).split()[2],16)
def setup(patched):
 n=Native();u=n.u
 n.w(0x6def58,0x1801000);n.w(0x6def5c,1)
 n.w(0x1801000+0xac,0x1803000);n.w(0x1803008,1);n.w(0x180300c,4);n.w(0x1803044,1)
 n.w(0x6e1f0c,1)
 if patched:
  u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
  u.mem_write(0x517a81,b'\xe9'+struct.pack('<i',hook-0x517a86)+b'\x90'*4)
 return n
def call(n,count,ret=0x4fefd0,centre=(54,74,5)):
 n.w(0x6e985c,count);u=n.u
 u.mem_write(0x20ff000,struct.pack('<8I',ret,*centre,0,0x1805000,0x1805004,0x1805008))
 u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_ECX,0x1801000)
 u.emu_start(0x517a50,ret,count=1000000)
 return struct.unpack('<3i',u.mem_read(0x1805000,12)),struct.unpack('<i',u.mem_read(0x6e985c,4))[0]

checks=0
# Original successful slots and exhausted fallback on a captured real map.
a,b=setup(False),setup(True)
for count in range(17):
 old=call(a,count);new=call(b,count)
 if old[0]!=(54,74,5) or count==0: assert old==new
 checks+=1
assert call(a,17)==((54,74,5),17)
assert call(b,17)==((54,73,6),18)
assert call(b,49)==call(a,49)
checks+=3
# Non-ground-click callers, multiplayer, width-two and special modes keep native.
for field,value,ret in [(0x6e1f0c,2,0x4fefd0),(0x1803008,2,0x4fefd0),
                        (0x1801104,1,0x4fefd0),(0x1803044,2,0x4fefd0),
                        (0x18015ec,14,0x4fefd0),(0x6e1f0c,1,0x4fe740),
                        (0x6e1f0c,1,0x4feb25),(0x6e1f0c,1,0x4ff0e5)]:
 a,b=setup(False),setup(True);a.w(field,value);b.w(field,value)
 for count in (0,1,16,17,32,49):assert call(a,count,ret)==call(b,count,ret);checks+=1
# Execute hook at every added slot, stopping at the unmodified native validator.
old={(0,0),(1,-1),(1,1),(-1,1),(-1,-1),(0,-2),(2,0),(0,2),(-2,0),
     (2,-2),(2,2),(-2,2),(-2,-2),(0,-4),(4,0),(0,4),(-4,0)}
for centre in ((40,40),(0,0),(79,79)):
 n=setup(True);u=n.u;points=set()
 for count in range(17,49):
  n.w(0x6e985c,count)
  stack=[0]*13;stack[5]=0x4fefd0;stack[6],stack[7]=centre;stack[8]=5
  stack[10]=0x1805000;stack[11]=0x1805004;stack[12]=0x1805008
  u.mem_write(0x20ff000,struct.pack('<13I',*stack))
  u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EBP,0x1801000)
  u.reg_write(UC_X86_REG_EAX,count);u.reg_write(UC_X86_REG_ESI,0x1805004)
  u.reg_write(UC_X86_REG_EDI,0x1805000);u.reg_write(UC_X86_REG_EBX,0x1805008)
  u.emu_start(hook,0x517b64,count=10000)
  assert u.reg_read(UC_X86_REG_ESP)==0x20ff000
  x,y=struct.unpack('<2i',u.mem_read(0x1805000,8))
  assert 0<=x<80 and 0<=y<80
  delta=(((x-centre[0]+40)%80)-40,((y-centre[1]+40)%80)-40)
  assert delta not in old and delta not in points and sum(v*v for v in delta)<=16
  points.add(delta);checks+=1
 assert len(old|points)==49
# A solid volume at all candidate layers is never accepted by native validation.
n=setup(True)
for z in (4,5,6):
 a=0x1000000+12*(54+80*73+6400*z)
 n.u.mem_write(a+10,struct.pack('<H',0x4000))
result,slot=call(n,17)
assert result[:2]!=(54,73) and slot>18
checks+=1
report=dict(result='passed',checks=checks,dll_sha256=i.sha(i.BUILD/'repath.dll'),
    evidence='Native test10 map: exhausted original centre fallback becomes supported (54,73,6); scope exclusions, solid rejection and 49 unique bounded toroidal offsets verified offline',gameplay_tested=False)
i.write(i.BUILD/'group-verification.json',report);print(report)
