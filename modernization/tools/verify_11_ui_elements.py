"""Offline x86 execution of actual page-sprite and tooltip adapters."""
import struct,json,hashlib
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2];BUILD=ROOT/'modernization/build/remastered-1.1-ui-elements'
p=pefile.PE(str(BUILD/'qol_bindings.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(BUILD/'qol_bindings.map').read_text(encoding='utf-8').splitlines()
def sym(name):return int(next(s for s in lines if '?'+name+'@' in s).split()[2],16)
regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
checks=0
class Fixture:
 def __init__(self,battle=False,port=False):
  self.u=Uc(UC_ARCH_X86,UC_MODE_32);u=self.u
  for a,size in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x100000)]:u.mem_map(a,size)
  u.mem_write(base,p.get_memory_mapped_image());self.put(0x6a49f0,2560,1440)
  table=[]
  if battle:
   for j,v in enumerate([0x5c6ee8,0x5c6f54]):
    control=0x2002000+j*0x100;self.put(control,v);self.put(control+0x11,0,0,1280,720);table.append(control)
  elif port:
   self.put(0x2002000,0x5c77f0);self.put(0x2002011,320,0,2240,1440);table.append(0x2002000)
  self.put(0x642c68,len(table))
  for j,c in enumerate(table):self.put(0x642034+j*4,c)
  self.calls=[]
  vq=next(i.address for d in p.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name==b'VirtualQuery')
  self.put(vq,0x2007000);u.hook_add(UC_HOOK_CODE,self.intercept)
 def put(self,a,*v):self.u.mem_write(a,struct.pack('<'+'I'*len(v),*[x&0xffffffff for x in v]))
 def get(self,a,n=1):return struct.unpack('<'+'i'*n,self.u.mem_read(a,n*4))
 def intercept(self,u,a,size,data):
  if a not in (0x2007000,0x2007010):return
  sp=u.reg_read(UC_X86_REG_ESP);ret=int.from_bytes(u.mem_read(sp,4),'little')
  if a==0x2007000:
   ptr,buf,n=struct.unpack('<3I',u.mem_read(sp+4,12));region=ptr&~0xffff
   self.put(buf,region,region,4,0x10000,0x1000,4,0x20000);argc=3;result=28
  else:
   control=u.reg_read(UC_X86_REG_ECX);self.calls.append(self.get(control+0x55)[0]);argc=0;result=0
  u.reg_write(UC_X86_REG_EAX,result);u.reg_write(UC_X86_REG_ESP,sp+4+argc*4);u.reg_write(UC_X86_REG_EIP,ret)
 def call(self,address,args=(),ecx=0):
  self.put(0x20ff000,0x20fe000,*args);self.u.reg_write(UC_X86_REG_ESP,0x20ff000);self.u.reg_write(UC_X86_REG_ECX,ecx)
  self.u.emu_start(address,0x20fe000,count=50000)
for battle in [False,True]:
 for active in [0,1]:
  for rect in [(147,1212,747,1318),(2180,1400,2780,1506),(400,300,1000,406),(0,0,0,0)]:
   f=Fixture(battle);tip=0x2001000;f.put(tip+4,active);f.put(tip+0x16a,*rect);f.put(tip+0x144,rect[0],rect[1]);f.put(0x6e1ee4,1234)
   for r,v in zip(regs,[123,234,345,456,tip,567,678]):f.u.reg_write(r,v)
   f.u.reg_write(UC_X86_REG_ESP,0x20ff000);f.u.reg_write(UC_X86_REG_EFLAGS,0x246)
   f.u.emu_start(sym('tooltip_destination_hook'),0x4db938,count=50000)
   expected=rect
   if not battle and active and rect[2]>rect[0]:
    w,h=rect[2]-rect[0],rect[3]-rect[1];x=min(max(320,rect[0]),2240-w);y=min(max(0,rect[1]),1440-h);expected=(x,y,x+w,y+h)
   assert f.get(tip+0x16a,4)==expected
   assert f.get(tip+0x144,2)==expected[:2]
   assert f.u.reg_read(UC_X86_REG_ESP)==0x20ff000 and f.u.reg_read(UC_X86_REG_EFLAGS)==0x246
   assert [f.u.reg_read(r) for r in regs]==[123,234,345,456,tip,1234,678];checks+=1
for battle,port in [(False,True),(False,False),(True,False)]:
 for frame in [0,16,21,43,54,73,99,102,107,233,234,-1]:
  for source_ok in [True,False]:
   f=Fixture(battle,port);control=0x2001000;original=0x2003000
   f.put(control,0x5c77bc);f.put(control+0x11,1292,52,1386,156);f.put(control+0x55,original if source_ok else original+100);f.put(control+0x59,frame)
   f.put(sym('original_icon_sprite'),original);f.put(sym('sprite_draw_original'),0x2007010)
   f.call(sym('port_icon_draw_hook'),ecx=control)
   selected=not battle and port and source_ok and 0<=frame<234
   assert f.calls==[sym('port_icon_sprite') if selected else original if source_ok else original+100],(battle,port,frame,f.calls)
   assert f.get(control+0x55)[0]==(original if source_ok else original+100)
   assert f.u.reg_read(UC_X86_REG_ESP)==0x20ff004;checks+=1
report=dict(checks=checks,result='passed',scope='actual compiled tooltip clamp/flags/stack and all-state page sprite substitution/restoration; battle/other containers unchanged',qol_sha256=hashlib.sha256((BUILD/'qol_bindings.dll').read_bytes()).hexdigest())
(BUILD/'ui-elements-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report)
