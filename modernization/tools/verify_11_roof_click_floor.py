"""Compiled Portmanteau keyboard dispatch/hover gate using save23 packed control rectangles."""
import struct,json,pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import build_11_roof_click_floor as b
OUT=b.OUT
checks=0
rows=json.loads((b.b.ROOT/'modernization/logs/remastered-ui/save23-bindings-before/slots.json').read_text())

def case(row,x,y,width=2560,height=1440,item=None,count_override=None,source=OUT):
 p=pefile.PE(str(source/'qol_bindings.dll'));base=p.OPTIONAL_HEADER.ImageBase
 lines=(source/'qol_bindings.map').read_text().splitlines()
 def sym(name):return int(next(x for x in lines if '?'+name+'@' in x).split()[2],16)
 imports={i.name.decode():struct.unpack('<I',p.get_data(i.address-base,4))[0] for g in p.DIRECTORY_ENTRY_IMPORT for i in g.imports if i.name}
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x300000)]:u.mem_map(a,n)
 u.mem_write(base,p.get_memory_mapped_image())
 for page in {v&~4095 for v in imports.values()}:u.mem_map(page,4096)
 def w(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
 def d(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 ui=0x2100000;result=0x2200000;stack=0x20ff000;end=0x20fe000
 w(0x6a49f0,width,height);w(ui+0x9c,x,y)
 for tray in range(3):
  n=max([r['index']+1 for r in rows if r['tray']==tray],default=0);ptr=0x2110000+tray*0x1000
  w(ui+0x84+tray*4,n);w(ui+0x218+tray*4,ptr)
  for r in rows:
   if r['tray']!=tray:continue
   c=ptr+r['index']*0x86;w(c+0x11,*r['rect']);w(c+0x7e,r['item'])
 if item is not None:w(0x2110000+row['tray']*0x1000+row['index']*0x86+0x7e,item)
 if count_override is not None:w(ui+0x84,count_override)
 w(0x6e1f0c,0);w(sym('bindings'),*([0xffffffff]*24));w(result,0xdeadbeef,0xdeadbeef);w(stack,end,ui,0x100,ord('Q'),0);u.reg_write(UC_X86_REG_ESP,stack)
 for r,v in [(UC_X86_REG_EBX,0xabc),(UC_X86_REG_ESI,0xdef),(UC_X86_REG_EDI,0x123),(UC_X86_REG_EBP,0x456)]:u.reg_write(r,v)
 def ret(argc,value=0):
  sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_EIP,d(sp));u.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
 def trace(u,a,size,data):
  sp=u.reg_read(UC_X86_REG_ESP)
  if a in (sym('load'),sym('save')):ret(0,1)
  elif a==sym('key_index'):ret(0,0)
  elif a==imports['GetEnvironmentVariableA']:ret(3,0)
  elif a==imports['PtInRect']:
   rect=struct.unpack('<4i',u.mem_read(d(sp+4),16));px=d(sp+8);py=d(sp+12)
   ret(3,int(rect[0]<=px<rect[2] and rect[1]<=py<rect[3]))
 u.hook_add(UC_HOOK_CODE,trace);u.emu_start(sym('on_event'),end,count=10000)
 assert u.reg_read(UC_X86_REG_ESP)==stack+4
 for r,v in [(UC_X86_REG_EBX,0xabc),(UC_X86_REG_ESI,0xdef),(UC_X86_REG_EDI,0x123),(UC_X86_REG_EBP,0x456)]:assert u.reg_read(r)==v
 out=u.reg_read(UC_X86_REG_EAX)&255;slot=(d(sym('bindings')),d(sym('bindings')+4));p.close();return out,slot

for row in rows:
 r=row['rect'];x=(r[0]+r[2])//2;y=(r[1]+r[3])//2
 assert case(row,x,y)==(1,(row['tray'],row['index']));checks+=1
 assert case(row,x,y,source=b.prev.SOURCE)[0]==0;checks+=1
 for x,y in [(r[0],r[1]),(r[2]-1,r[3]-1)]:
  assert case(row,x,y)==(1,(row['tray'],row['index']));checks+=1
 for item,expected in [(-1,1),(-2,0),(20,1),(21,0)]:
  assert case(row,(r[0]+r[2])//2,(r[1]+r[3])//2,item=item)[0]==expected;checks+=1
row=rows[0]
for w,h,x,y in [(2560,1440,319,1318),(2560,1440,2240,1318),(2560,1440,884,1440),(0,1440,884,1318),(9000,1440,884,1318),(2560,9000,884,1318)]:
 assert case(row,x,y,width=w,height=h)[0]==0;checks+=1
for w,h in [(1920,1440),(3840,2160),(5120,2880)]:
 assert case(row,884,1318,width=w,height=h)[0]==1;checks+=1
assert case(row,884,1318,count_override=22)[0]==0;checks+=1
# Preserve conditional click, roof control and portrait behavior in new module.
source=(b.b.ROOT/'modernization/tools/verify_11_canopy_pick.py').read_text()
source=source.replace('import build_11_canopy_pick as b','import build_11_roof_click_floor as b')
source=source.replace("replace('import build_11_roof_tab as b','import build_11_canopy_pick as b')", "replace('import build_11_roof_tab as b','import build_11_roof_click_floor as b')")
source=source.replace("replace('remastered-1.1-roof-tab','remastered-1.1-canopy-pick')", "replace('remastered-1.1-roof-tab','remastered-1.1-roof-click-floor')")
exec(compile(source,__file__,'exec'),{'__file__':__file__})
fixture_source=(b.b.ROOT/'modernization/tools/verify_11_canopy_pick.py').read_text().split('\nchecks=0\n')[0]
fixture_source=fixture_source.replace('import build_11_canopy_pick as b','import build_11_roof_click_floor as b')
ns={};exec(compile(fixture_source,__file__,'exec'),ns)
extra=0
for reachable,fog,count,expect in [(True,False,1,True),(True,False,2,True),(False,False,1,False),(True,True,1,False)]:
 u,w,d,call,events,edges,unit,scene=ns['fixture'](middle_reachable=reachable)
 # Solid floor at raw column (3,2,z1); target is standing layer2.
 tile=0x2200000+12*(3+8*(2+8*1));w(tile,1)
 w(0x2300000+356+0x94,16)
 if fog:u.mem_write(tile+11,b'\x40')
 w(ns['sym']('pick_count'),count)
 if count==1:w(ns['sym']('pick_cells'),3,2,3)
 call(ns['sym']('pick_movement_fallback'),[4])
 assert (d(0x6cbb64)==1)==expect,(reachable,fog,count,d(0x6cbb64))
 if expect:assert d(ns['sym']('pick_last_status'))==5
 extra+=1
# Projected floor can be absent from the opaque-hit stack, in all rotations.
for rot,xy in [(0,(2,1)),(1,(4,1)),(2,(4,3)),(3,(2,3))]:
 u,w,d,call,events,edges,unit,scene=ns['fixture'](middle_reachable=True)
 x,y=xy;tile=0x2200000+12*(x+8*(y+8));w(tile,1);w(0x2300000+356+0x94,16)
 w(ns['sym']('pick_count'),1);w(ns['sym']('pick_cells'),3,2,3)
 for n,v in [('pick_anchor_x',672),('pick_anchor_y',345),('pick_mouse_x',672),('pick_mouse_y',361),('pick_rotation',rot)]:w(ns['sym'](n),v)
 call(ns['sym']('pick_movement_fallback'),[4])
 assert d(ns['sym']('pick_last_status'))==6
 assert (d(0x6c5488),d(0x6c5484),d(0x6cbb64))==(x,y,1)
 extra+=1
# Per-pass floor candidate state clears and exact native sprite hit stays native.
u,w,d,call,events,edges,unit,scene=ns['fixture']()
w(ns['sym']('pick_surface_count'),8);call(ns['sym']('pick_begin'),[scene]);assert d(ns['sym']('pick_surface_count'))==0
w(scene+0x7d,3,2,3);w(scene+0x31,2);point=scene+0x91;w(point,672,361)
assert call(ns['sym']('canopy_mask'),[345,point],0x2410000,672,True)==1
assert d(ns['sym']('pick_anchor_y'))==345 and d(ns['sym']('pick_rotation'))==2
extra+=1
checks+=extra
other=json.loads((OUT/'verification.json').read_text())
b.base.write(OUT/'verification.json',dict(result='passed',checks=checks+other['checks'],hover_checks=checks,prior_input_checks=other['checks'],module_sha256=b.b.sha(OUT/'qol_bindings.dll'),scope='Lower floor and wall-edge footprint cases, fog rejection and native hit preservation; compiled save23 real packed rectangles, actual HD mouse positions, empty/item bounds, viewport bars/boundaries, future output sizes; PtInRect and config load/save doubles; actual on_event binding state/refresh executes. Previous conditional terrain/roof/main/teammate regressions. Native surface lifetime tests at build.',runtime_acceptance='pending user gameplay testing'))
print('Passed',checks+other['checks'],'checks')
