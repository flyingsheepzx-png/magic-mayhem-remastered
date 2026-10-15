"""Execute the real compiled map hooks offline; no game process."""
from pathlib import Path
import struct,json,hashlib
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'modernization/build/remastered-1.1-realm-fix'
pe=pefile.PE(str(BUILD/'qol_bindings.dll'));base=pe.OPTIONAL_HEADER.ImageBase
lines=(BUILD/'qol_bindings.map').read_text(encoding='utf-8').splitlines()
def symbol(name):return int(next(x for x in lines if '?'+name+'@' in x).split()[2],16)
checks=0
for w,h in [(1280,720),(2560,1440),(800,600),(3840,2160)]:
 for x,y in [(0,0),(100,100),(799,599),(800,600),(317,239)]:
  u=Uc(UC_ARCH_X86,UC_MODE_32)
  for a,size in [(0x400000,0x400000),(base,(pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000)]:u.mem_map(a,size)
  u.mem_write(base,pe.get_memory_mapped_image())
  def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*[n&0xffffffff for n in v]))
  put(0x6a49f0,w,h);put(0x2001000,x,y)
  put(0x20ff000,0x20fe000,0x2001000,0x2001004);u.reg_write(UC_X86_REG_ESP,0x20ff000)
  u.emu_start(symbol('project_realm_point'),0x20fe000,count=10000)
  actual=struct.unpack('<2i',u.mem_read(0x2001000,8))
  expected=((x*(12 if w==2560 else 6)+2)//5+(320 if w==2560 else 160),(y*(12 if w==2560 else 6)+2)//5) if w in (1280,2560) else (x,y)
  assert actual==expected,(w,x,y,actual,expected);checks+=1
  # Native hover expects local visual X only; preserve all other registers/flags.
  put(0x641abc,0x12345678)
  regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
  vals=[123,234,345,0,640,567,678]
  for r,v in zip(regs,vals):u.reg_write(r,v)
  u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EFLAGS,0x246)
  u.emu_start(symbol('realm_hover_hook'),0x5519a5,count=10000)
  wanted=vals[:];wanted[4]=640-(w-h*4//3)//2;wanted[5]=0x12345678
  assert [u.reg_read(r) for r in regs]==wanted,(w,[u.reg_read(r) for r in regs],wanted)
  assert u.reg_read(UC_X86_REG_ESP)==0x20ff000 and u.reg_read(UC_X86_REG_EFLAGS)==0x246;checks+=1
  # Real outline/enemy register adapters call the same projection function.
  for name,resume in [('realm_outline_hook',0x4a2e1e),('realm_enemy_hook',0x550bc9)]:
   put(0x2002000+0x1db,999)
   for r,v in zip(regs,vals):u.reg_write(r,v)
   u.reg_write(UC_X86_REG_EBX,0x2002000);u.reg_write(UC_X86_REG_ECX,x);u.reg_write(UC_X86_REG_ESI,y)
   u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EFLAGS,0x246)
   u.emu_start(symbol(name),resume,count=10000)
   assert (u.reg_read(UC_X86_REG_ECX),u.reg_read(UC_X86_REG_ESI))==expected,(name,w,expected)
   assert u.reg_read(UC_X86_REG_ESP)==0x20ff000;checks+=1
# Keyed rectangle blit uses full destination bounds, preserves source crop,
# returns to native path for unrelated sources/unsupported surfaces/failure.
for w,h in [(1280,720),(2560,1440),(3840,2160)]:
 for matching,hr in [(True,0),(False,0),(True,0x80004005)]:
  u=Uc(UC_ARCH_X86,UC_MODE_32)
  for a,size in [(0x400000,0x400000),(base,(pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000)]:u.mem_map(a,size)
  u.mem_write(base,pe.get_memory_mapped_image())
  def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*[n&0xffffffff for n in v]))
  put(0x6a49f0,w,h)
  src,dst,crop,srcobj,dstobj,vt=0x2001000,0x2002000,0x2003000,0x2004000,0x2005000,0x2006000
  put(symbol('realm_highlight_source'),src if matching else 0)
  put(src+8,srcobj);put(dst+8,dstobj);put(dstobj,vt);put(vt+20,0x2007000)
  put(crop,5,7,25,37)
  env=next(i.address for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name==b'GetEnvironmentVariableA')
  put(env,0x2007010);calls=[]
  def intercept(uc,address,size,data):
   if address not in (0x2007000,0x2007010):return
   sp=uc.reg_read(UC_X86_REG_ESP)
   args=struct.unpack('<7I',uc.mem_read(sp,28))
   if address==0x2007000:
    target=struct.unpack('<4i',uc.mem_read(args[2],16));sourcecrop=struct.unpack('<4i',uc.mem_read(args[4],16))
    calls.append((target,sourcecrop,args[5]));result=hr;argc=6
   else:result=0;argc=3
   uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_ESP,sp+4+argc*4);uc.reg_write(UC_X86_REG_EIP,args[0])
  u.hook_add(UC_HOOK_CODE,intercept)
  put(0x20ff000,0x20fe000,src,dst,crop,100,200);u.reg_write(UC_X86_REG_ESP,0x20ff000)
  u.emu_start(symbol('draw_projected_highlight'),0x20fe000,count=20000)
  active=matching and w in (1280,2560)
  assert u.reg_read(UC_X86_REG_EAX)==int(active and hr==0)
  assert len(calls)==int(active)
  if active:
   num,origin=(12,320) if w==2560 else (6,160)
   expect=((100*num+2)//5+origin,(200*num+2)//5,(120*num+2)//5+origin,(230*num+2)//5)
   assert calls==[(expect,(5,7,25,37),0x01008000)],calls
  checks+=1
report=dict(checks=checks,result='passed',scope='real compiled x86 project/hover/outline/enemy/keyed highlight blit; unsupported output guard',qol_sha256=hashlib.sha256((BUILD/'qol_bindings.dll').read_bytes()).hexdigest())
(BUILD/'realm-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report)
