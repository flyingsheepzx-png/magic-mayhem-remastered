"""Execute compiled reveal pass and real native RLE rasterizer offline."""
import json
import struct
import pefile
from unicorn.x86_const import *
from emulate_terrain_diagonal import Native
from install_occluded_body import installer as i

p=pefile.PE(str(i.BUILD/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(i.BUILD/'repath.map').read_text().splitlines()
def sym(name):return int(next(x for x in lines if '?'+name+'@@' in x).split()[2],16)
buffer=0x1808000;sprite=0x1804000;palette=0x1400000
context=(0x658174,0x6a2dc8,0x6def50,0x6cbb6c,0x6e0008,0x6a49b8,0x656618)

def setup():
    n=Native();u=n.u
    u.reg_write(UC_X86_REG_FPCW,0x37f);u.reg_write(UC_X86_REG_MXCSR,0x1f80)
    u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
    u.mem_write(base,p.get_memory_mapped_image())
    for name,v in [('frame_width',8),('frame_height',8),('frame_row_bytes',16),('pitch',20),('command_count',1)]:n.w(sym(name),v)
    u.mem_write(sym('clip'),struct.pack('<4i',1,1,7,7))
    u.mem_write(sym('captured'),b'\1');u.mem_write(sym('occluded_units_enabled'),b'\1')
    n.w(0x6e1f0c,1);u.mem_write(sym('body_commands'),b'\1');n.w(sym('owners'),0)
    for off,v in [(4,4),(8,4),(0x1c,palette)]:n.w(sprite+off,v)
    n.w(palette+4,0);n.w(palette+8,127)
    u.mem_write(palette+12+127*512+2,struct.pack('<H',0xf800))
    for row in range(4):
        n.w(sprite+0x28+row*8,0x80+row*8);n.w(sprite+0x2c+row*8,0x84+row*8)
        u.mem_write(sprite+0x80+row*8,b'\1\2\1');u.mem_write(sprite+0x84+row*8,b'\1\1')
    c=bytearray(36);struct.pack_into('<3i',c,4,sprite,2,2)
    struct.pack_into('<2h',c,0x1c,-30000,-30000);u.mem_write(sym('saved'),bytes(c))
    image=[[0x001f]*8+[0xa55a]*2 for _ in range(8)]
    for y in range(2,6):image[y][3]=0xf800
    u.mem_write(buffer,b''.join(struct.pack('<10H',*row) for row in image))
    for j,a in enumerate(context):n.w(a,0x123400+j)
    return n,image

def run(n,fraction=0.0):
    u=n.u
    u.mem_write(0x20ff000,struct.pack('<IId',0x20fe000,buffer,fraction))
    u.reg_write(UC_X86_REG_ESP,0x20ff000)
    try:u.emu_start(sym('draw_occluded_units'),0x20fe000,count=1000000)
    except Exception:
        print('EIP',hex(u.reg_read(UC_X86_REG_EIP)),'stack',bytes(u.mem_read(u.reg_read(UC_X86_REG_ESP),24)).hex());raise
    assert u.reg_read(UC_X86_REG_ESP)==0x20ff004
    assert all(struct.unpack('<I',u.mem_read(a,4))[0]==0x123400+j for j,a in enumerate(context))
    return [list(struct.unpack('<10H',u.mem_read(buffer+y*20,20))) for y in range(8)]

checks=0
n,expected=setup()
for y in range(2,6):expected[y][4]=0x780f
assert run(n)==expected;checks+=1
# Lower, floor-clipped body pixels must remain concealed.
n,expected=setup();n.u.mem_write(sym('saved')+0x1c,struct.pack('<h',-2))
for y in range(2,4):expected[y][4]=0x780f
assert run(n)==expected;checks+=1
# Viewport edges and transparent RLE gaps stay exact, including row padding.
n,expected=setup();n.u.mem_write(sym('clip'),struct.pack('<4i',4,3,5,5))
for y in (3,4):expected[y][4]=0x780f
assert run(n)==expected;checks+=1
for name,offset,v,size in [('occluded_units_enabled',0,0,1),('captured',0,0,1),
    ('command_count',0,0,4),('body_commands',0,0,1),('owners',0,-1,4),
    ('saved',0x18,1,4),('saved',0x12,-1,2),('saved',0x1e,0,2),
    ('saved',0x10,128,2)]:
    n,expected=setup();n.u.mem_write(sym(name)+offset,v.to_bytes(size,'little',signed=True))
    assert run(n)==expected;checks+=1
for address,v in [(0x6e1f0c,2),(sprite+0x1c,-1),(sprite+4,0),(sprite+8,1025)]:
    n,expected=setup();n.w(address,v);assert run(n)==expected;checks+=1
# An ordinary body in front replaces a ghost behind it in the private pass.
n,expected=setup();n.w(sym('command_count'),2)
c=bytearray(n.u.mem_read(sym('saved'),36));struct.pack_into('<i',c,8,3)
n.u.mem_write(sym('saved')+36,bytes(c));n.u.mem_write(sym('body_commands')+1,b'\1');n.w(sym('owners')+4,0)
for y in range(2,6):
    expected[y][4]=0xf800
    n.u.mem_write(buffer+y*20+8,struct.pack('<H',0xf800))
    expected[y][5]=0x780f
assert run(n)==expected;checks+=1
# Replay uses the same world-to-screen offsets as the ordinary sprite pass.
for rotation,dx,dy in [(0,2,1),(1,2,-1),(2,-2,-1),(3,-2,1)]:
    n,_=setup();n.w(sym('rotation'),rotation);n.w(sym('actors')+16,4)
    expected=[[0x001f]*8+[0xa55a]*2 for _ in range(8)]
    for y in range(2+dy,6+dy):
        if 1<=y<7 and 1<=3+dx<7:expected[y][3+dx]=0xf800
    n.u.mem_write(buffer,b''.join(struct.pack('<10H',*row) for row in expected))
    for y in range(2+dy,6+dy):
        if 1<=y<7 and 1<=4+dx<7:expected[y][4+dx]=0x780f
    assert run(n,0.5)==expected;checks+=1
tag_fn=int(next(x for x in lines if ' _mm_render_tag ' in x).split()[2],16)
for site,mode,alive,active,want in [(0x4fa622,0,1,1,1),(0x4fa622,1,1,1,0),
    (0x4fa703,0,1,1,1),(0x4fa703,31,1,1,1),(0x4fa7c9,31,1,1,1),(0x4fa703,1,1,1,0),(0x4fa849,31,1,1,0),(0x4fa622,0,0,1,0),(0x4fa622,0,1,0,0)]:
    n,_=setup();stack=0x1801000;queue=0x1802000;command=0x1803000;actor=0x1806000
    n.w(0x6def58,actor);n.w(0x6def5c,1)
    n.w(actor+4,active);n.w(actor+0xe4,alive)
    n.w(stack+4,site);n.w(stack+0x5c,actor)
    n.w(queue+4,command+36);n.w(queue+8,1);n.w(command+0x18,mode)
    n.call(tag_fn,[stack,queue])
    assert bytes(n.u.mem_read(sym('body_tags'),1))==bytes([want]);checks+=1
report=dict(result='passed',checks=checks,dll_sha256=i.sha(i.BUILD/'repath.dll'),
 evidence='Compiled reveal pass, native RLE rasterizer and body tagging: half blend, unchanged visible pixels, transparency, floor/viewport clipping, padding, context restore, overlap, four-view replay offsets and exclusions',gameplay_tested=False)
i.write(i.BUILD/'occlusion-verification.json',report);print(json.dumps(report))
