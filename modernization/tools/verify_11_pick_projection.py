"""Native picker traversal and compiled fallback; no live game input."""
import json,struct,pefile
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import build_11_pick_projection as b

# Preserve existing conditional gates, bindings, roof and portrait tests.
source=(b.b.ROOT/'modernization/tools/verify_11_port_bindings_hd.py').read_text(encoding='utf-8')
source=source.replace('import build_11_port_bindings_hd as b','import build_11_pick_projection as b')
source=source.replace("import build_11_port_bindings_hd as b')","import build_11_pick_projection as b')")
source=source.replace('remastered-1.1-port-bindings-hd','remastered-1.1-pick-projection')
source=source.replace('source=b.SOURCE','source=b.prev.prev.SOURCE')
source=source.replace(' def sym(name):',' from functools import cache\n @cache\n def sym(name):')
exec(compile(source,__file__,'exec'),{'__file__':__file__})
report=json.loads((b.OUT/'verification.json').read_text());checks=0
source=(b.b.ROOT/'modernization/tools/verify_11_canopy_pick.py').read_text().split('\nchecks=0\n')[0].replace('import build_11_canopy_pick as b','import build_11_pick_projection as b')
source=source.replace('def sym(name):','from functools import cache\n@cache\ndef sym(name):')
ns={};exec(compile(source,__file__,'exec'),ns)
sym=ns['sym'];engine=pefile.PE(str(ns['engine']))
native_rows=[]
# Execute actual4f83f0 traversal/4f8230 camera origin in all rotations.
# Tile sprite handling4f8960 is an explicit capture-only double. Traversal,
# anchors and returned raw cell coordinates are actual native instructions.
for rot in range(4):
 u,w,d,call,*rest=ns['fixture']();scene=rest[-1];dim=0x2430000;world=0x2440000;rect=0x2420000
 u.mem_write(0x400000,engine.get_memory_mapped_image())
 w(dim,0,8,8,4,64);w(world+0x4c,0x2200000);w(world+0x7f0,0)
 for z in range(4):w(world+0x6432+4*z,z*64)
 for y in range(8):w(world+0x64b2+4*y,y*8)
 for off,val in [(0x11,100),(0x15,100),(0x21,world),(0x25,dim),(0x31,rot),(0x39,3),(0x3d,3),(0x41,2),(0x45,0),(0x49,0),(0x4d,0),(0x51,0),(0x55,0),(0x59,4),(0x5d,2),(0x61,4),(0x6d,1),(0x71,0),(0xad,4)]:w(scene+off,val)
 w(rect,(-4096)&0xffffffff,(-4096)&0xffffffff,4096,4096)
 captured=[]
 def trace(uc,a,size,data):
  if a==0x4f8960:
   captured.append(tuple(d(scene+o) for o in (0x7d,0x81,0x85,0x89,0x8d)))
   sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EIP,d(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
 u.hook_add(UC_HOOK_CODE,trace);call(0x4f83f0,[rect],scene,0,True)
 table={r[:3]:r[3:] for r in captured}
 assert table
 for (x,y,z),(sx,sy) in table.items():
  if (x+1,y,z) in table:assert table[(x+1,y,z)]==(sx+32,sy+16);checks+=1
  if (x,y+1,z) in table:assert table[(x,y+1,z)]==(sx-32,sy+16);checks+=1
  if (x,y,z+1) in table:assert table[(x,y,z+1)]==(sx,sy-16);checks+=1
 native_rows.append(dict(rotation=rot,tiles=len(captured),grid_axes=[[32,16],[-32,16]],height_step=-16))

def projected_case(rot,ix,iy,fog=False,reachable=True,offset=(0,0),raw_reachable=False):
 u,w,d,call,events,edges,unit,scene=ns['fixture'](middle_reachable=reachable,raw_reachable=raw_reachable,behind_reachable=False)
 w(sym('pick_count'),1);w(sym('pick_cells'),3,2,3)
 tx=(3+ix)%8;ty=(2+iy)%8
 tile=0x2200000+12*(tx+8*(ty+8));w(tile,1);w(0x2300000+356+0x94,16)
 if fog:u.mem_write(tile+11,b'\x40')
 for name,val in [('pick_anchor_x',672),('pick_anchor_y',345),('pick_mouse_x',672+32*(ix-iy)+offset[0]),('pick_mouse_y',345+16*(ix+iy)+16+offset[1]),('pick_rotation',rot)]:w(sym(name),val)
 call(sym('pick_movement_fallback'),[4]);return u,w,d,call,events,(tx,ty,1)

for rot in range(4):
 for ix,iy in [(0,0),(1,0),(0,1),(-1,0),(0,-1),(-3,-2),(5,6)]:
  for offset in [(0,0),(5,2),(-5,-2)]:
   u,w,d,call,events,expected=projected_case(rot,ix,iy,offset=offset)
   assert tuple(d(a) for a in (0x6c5488,0x6c5484,0x6cbb64))==expected,(rot,ix,iy,offset)
   assert d(sym('pick_last_status'))==6;checks+=1
 # Same-column reachable surface must NOT hijack a pixel over adjacent floor.
 u,w,d,call,events,expected=projected_case(rot,1,0)
 w(0x6c5488,3);w(0x6c5484,2);w(0x6cbb64,3)
 w(0x2200000+12*(3+8*(2+8)),1)
 call(sym('pick_movement_fallback'),[4])
 assert tuple(d(a) for a in (0x6c5488,0x6c5484,0x6cbb64))==expected;checks+=1
for kw in [dict(fog=True),dict(reachable=False),dict(raw_reachable=True)]:
 u,w,d,call,events,expected=projected_case(1,1,0,**kw)
 assert d(0x6cbb64)==3 and not events;checks+=1
for rot in range(4):
 for ox,oy in [(32,0),(-32,0),(31,0),(-33,0),(0,16),(0,-16),(20,10),(-20,-10),(12,-6),(6,12)]:
  u,w,d,call,events,expected=projected_case(rot,0,0,offset=(ox,oy))
  for y in range(8):
   for x in range(8):w(0x2200000+12*(x+8*(y+8)),1)
  w(0x6c5488,3);w(0x6c5484,2);w(0x6cbb64,3)
  call(sym('pick_movement_fallback'),[4])
  ix=(2*oy+ox+32)//64;iy=(2*oy-ox+32)//64
  assert tuple(d(a) for a in (0x6c5488,0x6c5484,0x6cbb64))==((3+ix)%8,(2+iy)%8,1)
  assert d(sym('pick_surface_count'))==1;checks+=1

# Real captured save24 terrain and native514360; only Windows/readability calls
# use doubles. The original wrong floor must be replaced by adjacent97,96,7.
import analyze_test18_corridor as a
n=a.Terrain();capture=b.b.ROOT/'modernization/logs/remastered-ui/save24-pick-final-v2'
n.u.mem_write(0x1000000,(capture/'map.bin').read_bytes());n.u.mem_write(0x1400000,(capture/'tile-types.bin').read_bytes());n.u.mem_write(n.unit,(capture/'unit0.bin').read_bytes());n.w(n.unit+0xac,n.typ)
for addr,val in [(0x6c5494,100),(0x6c5498,100),(0x6c549c,16),(0x6c54a0,10000),(0x5e1780,16),(0x6903e8,1),(0x6a5134,1),(0x644520,1)]:n.w(addr,val)
for y in range(100):n.w(0x6cb942+4*y,100*y)
for z in range(16):n.w(0x6cb8c2+4*z,10000*z)
n.w(n.unit+0x68,1)
p=ns['p'];base=ns['base'];n.u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(base,p.get_memory_mapped_image())
for page in {v&~4095 for v in ns['imports'].values()}:n.u.mem_map(page,4096)
def read(addr):return struct.unpack('<I',n.u.mem_read(addr,4))[0]
def trace(uc,addr,size,data):
 if addr==ns['imports']['VirtualQuery']:
  sp=uc.reg_read(UC_X86_REG_ESP);ptr=read(sp+8);n.w(ptr,read(sp+4));n.w(ptr+8,4);n.w(ptr+12,0x100000);n.w(ptr+16,0x1000);n.w(ptr+20,4)
  uc.reg_write(UC_X86_REG_EAX,28);uc.reg_write(UC_X86_REG_EIP,read(sp));uc.reg_write(UC_X86_REG_ESP,sp+16);return
 if addr==sym('readable') or addr==ns['imports']['GetKeyState'] or addr==0x4a3c70:
  argc=1 if addr==ns['imports']['GetKeyState'] else 0
  sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EAX,0 if argc else 1);uc.reg_write(UC_X86_REG_EIP,read(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
n.u.hook_add(UC_HOOK_CODE,trace)
for rot in range(4):
 n.w(0x6c5488,99);n.w(0x6c5484,97);n.w(0x6cbb64,9)
 for name,values in [('pick_count',[1]),('pick_cells',[99,97,9]),('pick_map',[0x1000000]),('pick_anchor_x',[704]),('pick_anchor_y',[360]),('pick_mouse_x',[684]),('pick_mouse_y',[338]),('pick_rotation',[rot])]:
  for i,v in enumerate(values):n.w(sym(name)+4*i,v)
 try:n.call(sym('pick_movement_fallback'),[4],0,20000000)
 except Exception:
  print('Native fixture failure EIP',hex(n.u.reg_read(UC_X86_REG_EIP)),'ESP',hex(n.u.reg_read(UC_X86_REG_ESP)));raise
 assert tuple(read(a) for a in (0x6c5488,0x6c5484,0x6cbb64))==(97,96,6),(rot,tuple(read(a) for a in (0x6c5488,0x6c5484,0x6cbb64)),read(sym('pick_last_status')))
 assert read(sym('pick_last_status'))==6;checks+=1
report.update(result='passed',projection_checks=checks,native_traversal=native_rows,save24_native_destination=[97,96,7],module_sha256=b.b.sha(b.OUT/'qol_bindings.dll'),runtime_acceptance='pending user testing; no live game launched',projection_evidence='Native4f83f0 traversal axes,4f8230 camera origin,4f8c3e direct picker coordinates, native cursor16 support height. Real saved terrain native514360; Windows APIs and tile sprite capture explicit doubles.')
b.base.write(b.OUT/'verification.json',report);print(json.dumps(report,indent=2))
