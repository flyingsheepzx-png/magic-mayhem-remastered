import struct,json,pefile
from emulate_terrain_diagonal import Native
from unicorn.x86_const import *
from install_speech_layout import installer as i
p=pefile.PE(str(i.BUILD/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(i.BUILD/'repath.map').read_text().splitlines();hook=int(next(x for x in lines if '?speech_hook@@' in x).split()[2],16)
cases=0
for w,h in [(800,600),(1280,720),(1920,1080),(2560,1440)]:
 for mode in ['normal','multiplayer','dialog','dynamic','ambiguous','disabled']:
  n=Native();u=n.u;u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
  surface=0x1801000;desc=0x1802000
  n.w(0x6e1f0c,2 if mode=='multiplayer' else 1);n.w(0x6de6d5,1);n.w(0x6a49f0,w);n.w(0x6a49f4,h)
  n.w(desc+12,2 if mode=='dialog' else 4);u.mem_write(desc+0x30,b'\0' if mode=='dynamic' else b'\1')
  n.w(surface+0x20,460);n.w(surface+0x24,300);n.w(0x6a2dd0+0x1518,3)
  for j in range(3):
   icon=0x6a2dd0+0xfc+j*0xc6;n.w(icon+0x3d,0 if j==1 else 2)
   u.mem_write(icon+0x11,struct.pack('<4i',w-296,h-50,w-256,h-6))
  if mode=='ambiguous':n.w(0x6a2dd0+0xfc+0x3d,0)
  if mode=='disabled':n.w(0x6a2dd0+0xfc+0xc6+0x3d,2)
  regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
  vals=[123,234,345,456,desc,567,surface]
  for r,v in zip(regs,vals):u.reg_write(r,v)
  u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_EFLAGS,0x246)
  u.emu_start(hook,0x573373,count=50000)
  xy=struct.unpack('<2i',u.mem_read(surface+0x20,8))
  assert xy==((w-476,h-370) if mode=='normal' else (460,300)),(mode,xy)
  assert u.reg_read(UC_X86_REG_ESP)==0x20ff000 and u.reg_read(UC_X86_REG_EFLAGS)==0x246
  assert all(u.reg_read(r)==(1 if r==UC_X86_REG_ECX else v) for r,v in zip(regs,vals)), [(r,u.reg_read(r),v) for r,v in zip(regs,vals)]
  cases+=1
report=dict(checks=cases,result='passed',dll_sha256=i.sha(i.BUILD/'repath.dll'))
i.write(i.BUILD/'speech-verification.json',report);print(report)

