"""Compiled conditional occlusion fallback with bounded native-edge fixtures."""
import struct,pefile,json
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import build_11_canopy_pick as b
OUT=b.OUT
engine=b.base.DEST/'runtime/Chaos-Wide169-engine.exe'
assert b.b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
p=pefile.PE(str(OUT/'qol_bindings.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(OUT/'qol_bindings.map').read_text().splitlines()
def sym(name):return int(next(x for x in lines if '?'+name+'@' in x).split()[2],16)
imports={x.name.decode():struct.unpack('<I',p.get_data(x.address-base,4))[0] for group in p.DIRECTORY_ENTRY_IMPORT for x in group.imports if x.name}

def fixture(mode=1,kind=1,flags=4,players=1,modifier=0,raw_reachable=False,behind_reachable=True,selected=True,stale=False,middle_reachable=False):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x500000)]:u.mem_map(a,n)
 u.mem_write(base,p.get_memory_mapped_image())
 for page in {v&~4095 for v in imports.values()}:u.mem_map(page,4096)
 def w(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
 def d(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 stack=0x20ff000;end=0x20fe000;unit=0x2100000;utype=0x2110000;mapaddr=0x2200000;types=0x2300000;scene=0x2400000
 w(0x6e1f0c,players);w(0x6903e8,mode);w(0x6a5134,kind);w(0x6c5494,8,8,4);w(0x6c54dc,mapaddr);w(0x65660c,types)
 w(0x6def5c,1);w(0x6def58,unit);w(0x644520,0);w(unit+4,1,2,2,1);w(unit+0xe4,1);w(unit+0x68,int(selected));w(unit+0xac,utype);w(utype+8,1);w(utype+0x44,1)
 w(0x6c5488,3);w(0x6c5484,2);w(0x6cbb64,3)
 w(sym('pick_count'),2);w(sym('pick_cells'),3,2,1,3,2,3);w(sym('pick_map'),mapaddr+int(stale))
 events=[];edges=[]
 def ret(argc,value=0):
  sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_EIP,d(sp));u.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
 def trace(u,a,size,data):
  sp=u.reg_read(UC_X86_REG_ESP)
  if a==0x514360:
   v=[d(sp+4+i*4) for i in range(8)];frm=tuple(v[:3]);to=tuple(v[3:6]);edges.append((frm,to));w(v[6],0)
   allow=(to[2]==1 and behind_reachable) or (to[2] in (2,3) and raw_reachable) or (to[2]==2 and middle_reachable)
   ret(8,int(allow))
  elif a==0x4a3c70:events.append('cursor');ret(0,1)
  elif a==sym('readable'):ret(0,1)
  elif a==imports['VirtualQuery']:
   q=d(sp+8);w(q,d(sp+4),d(sp+4),4,0x100000,0x1000,4,0x20000);ret(3,28)
  elif a==imports['GetKeyState']:ret(1,modifier)
  elif a==0x57dcf0:events.append(('mask',u.reg_read(UC_X86_REG_ECX),u.reg_read(UC_X86_REG_EDX),d(sp+4),d(sp+8)));ret(2,1)
 u.hook_add(UC_HOOK_CODE,trace)
 def call(entry,args=(),ecx=0,edx=0,fastcall=False):
  w(stack,end,*args);u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,ecx);u.reg_write(UC_X86_REG_EDX,edx)
  for r,v in [(UC_X86_REG_EBX,0xabc),(UC_X86_REG_ESI,0xdef),(UC_X86_REG_EDI,0x123),(UC_X86_REG_EBP,0x456)]:u.reg_write(r,v)
  u.emu_start(entry,end,count=1000000)
  assert u.reg_read(UC_X86_REG_ESP)==stack+4+(len(args)*4 if fastcall else 0)
  for r,v in [(UC_X86_REG_EBX,0xabc),(UC_X86_REG_ESI,0xdef),(UC_X86_REG_EDI,0x123),(UC_X86_REG_EBP,0x456)]:assert u.reg_read(r)==v
  return u.reg_read(UC_X86_REG_EAX)
 return u,w,d,call,events,edges,unit,scene

checks=0
for kwargs,expect in [(dict(),True),(dict(raw_reachable=True),False),(dict(behind_reachable=False),False),(dict(mode=2),False),(dict(mode=0),False),(dict(mode=3),False),(dict(kind=2),False),(dict(kind=3),False),(dict(flags=2),False),(dict(players=2),False),(dict(modifier=0x8000),False),(dict(selected=False),False),(dict(stale=True),False)]:
 u,w,d,call,events,edges,unit,scene=fixture(**kwargs)
 call(sym('pick_movement_fallback'),[kwargs.get('flags',4)])
 assert (d(0x6cbb64)==1)==expect,(kwargs,d(0x6cbb64),d(sym('pick_last_status')))
 assert bool(events)==expect
 if expect:assert d(sym('pick_last_status'))==4
 checks+=1
# Native rendering/mask hit never changes; terrain candidates reset per pass.
u,w,d,call,events,edges,unit,scene=fixture()
call(sym('pick_begin'),[scene]);assert d(sym('pick_count'))==0
w(scene+0x7d,3,2,3);point=scene+0x91;sprite=0x2410000
assert call(sym('canopy_mask'),[345,point],sprite,672,True)==1
assert d(sym('pick_count'))==1 and events[-1]==('mask',sprite,672,345,point)
assert call(sym('canopy_mask'),[345,point],sprite,672,True)==1 and d(sym('pick_count'))==1
w(scene+0x85,1);call(sym('canopy_mask'),[345,point],sprite,672,True);assert d(sym('pick_count'))==2
call(sym('pick_begin'),[scene]);assert d(sym('pick_count'))==0
checks+=5
# Unknown due to exhausted search budget must not report unreachable.
u,w,d,call,events,edges,unit,scene=fixture()
budget=0x2420000;w(budget,0)
result=call(sym('pick_reachable'),[unit,3,2,3,budget]);assert result==0xffffffff
checks+=1
source=(b.b.ROOT/'modernization/tools/verify_11_roof_tab.py').read_text()
source=source.replace('import build_11_roof_tab as b','import build_11_canopy_pick as b').replace('remastered-1.1-roof-tab','remastered-1.1-canopy-pick')
exec(compile(source,__file__,'exec'),{'__file__':__file__})
other=json.loads((OUT/'verification.json').read_text())
b.base.write(OUT/'verification.json',dict(result='passed',checks=checks+other['checks'],conditional_pick_checks=checks,module_sha256=b.b.sha(OUT/'qol_bindings.dll'),prior_input_checks=other['checks'],scope='Compiled fallback decision, actual-hit candidate ordering and reset, fastcall mask forwarding, unreachable/reachable/unknown search states, spell/unit/item/modifier/multiplayer/selection/stale gates; transition callback uses synthetic topology. Existing native roof/portrait regression suite.',runtime_acceptance='pending user gameplay testing'))
print('Passed',checks+other['checks'],'checks');p.close()
