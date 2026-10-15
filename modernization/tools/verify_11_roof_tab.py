"""Compiled Tab adapter/hook plus actual native roof callback; no gameplay."""
import struct,pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import build_11_roof_tab as b
OUT=b.OUT
engine=b.base.DEST/'runtime/Chaos-Wide169-engine.exe'
assert b.b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
e=pefile.PE(str(engine));p=pefile.PE(str(OUT/'qol_bindings.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(OUT/'qol_bindings.map').read_text().splitlines()
def sym(name):return int(next(x for x in lines if '?'+name+'@' in x).split()[2],16)
imports={x.name.decode():struct.unpack('<I',p.get_data(x.address-base,4))[0] for group in p.DIRECTORY_ENTRY_IMPORT for x in group.imports if x.name}
def case(state=1,count=2,mode=1,repeat=False,key=9,modifier=0,players=1,hook=False):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x300000)]:u.mem_map(a,n)
 u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
 for page in {v&~4095 for v in imports.values()}:u.mem_map(page,4096)
 def w(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
 def d(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 owner=0x2100000;terrain=0x2200000;stack=0x20ff000;end=0x20fe000
 w(0x6e1f0c,players);w(0x689995,state);w(0x689999,count);w(0x68999d,mode);w(0x689955,terrain)
 w(terrain+12,count);w(owner+0x100b3,0x2210000);w(0x689965,99);w(0x6cbb70,123)
 flags=(1<<30) if repeat else 0
 if hook:
  w(stack,*([0]*30));w(stack+0x10,owner);w(stack+0x34,flags)
  u.reg_write(UC_X86_REG_ESI,key);u.reg_write(UC_X86_REG_EAX,key)
  entry=sym('battle_key_hook')
 else:
  w(stack,end,key,flags,owner);entry=sym('roof_tab')
 u.reg_write(UC_X86_REG_ESP,stack);events=[]
 def ret(argc,value=0):
  sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_EIP,d(sp));u.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
 def trace(u,a,size,data):
  sp=u.reg_read(UC_X86_REG_ESP)
  if a==sym('readable'):ret(0,1)
  elif a==imports['GetKeyState']:ret(1,modifier)
  elif a==0x46fc50:events.append(('native-roof',u.reg_read(UC_X86_REG_ECX),d(sp+4)))
  elif a==0x4cb7d0:events.append(('button',d(sp+4),d(sp+8),d(sp+12)));ret(3)
  elif a==0x56c060:ret(3)
  elif hook and a in (0x46e086,0x46c19a):u.emu_stop()
 u.hook_add(UC_HOOK_CODE,trace);u.emu_start(entry,end,count=10000)
 if hook:
  assert u.reg_read(UC_X86_REG_EIP)==0x46e086 and u.reg_read(UC_X86_REG_ESP)==stack
  assert u.reg_read(UC_X86_REG_ESI)==key and u.reg_read(UC_X86_REG_EAX)==key
 else:assert u.reg_read(UC_X86_REG_EIP)==end and u.reg_read(UC_X86_REG_ESP)==stack+4
 return events,d(0x689995),d(0x689991),u.reg_read(UC_X86_REG_EAX)
checks=0
for count in (2,3):
 for state in range(1,count+1):
  for mode in (0,1):
   events,new_state,layer,result=case(state,count,mode)
   assert result==1 and events[0]==('native-roof',0x2100000,0)
   assert (new_state if mode else layer)==state%count+1
   checks+=1
for kw in [dict(repeat=True),dict(key=65),dict(modifier=0x8000),dict(players=2),dict(count=0)]:
 events,state,layer,result=case(**kw);assert not events and state==1
 assert result==(1 if kw.get('repeat') else 0);checks+=1
for repeat in (False,True):
 events,state,layer,_=case(hook=True,repeat=repeat)
 assert state==(1 if repeat else 2) and bool(events)==(not repeat);checks+=1
# Existing main/teammate regressions run on this module, preserving their checks.
source=(b.b.ROOT/'modernization/tools/verify_11_main_portrait_cancel.py').read_text()
source=source.replace('remastered-1.1-main-portrait-cancel','remastered-1.1-roof-tab')
source=source.replace("build.OUT/'qol_bindings.dll'","OUT/'qol_bindings.dll'")
exec(compile(source,__file__,'exec'),{'__file__':__file__,'OUT':OUT})
import json
other=json.loads((OUT/'verification.json').read_text())
b.base.write(OUT/'verification.json',dict(result='passed',checks=checks+other['checks'],roof_checks=checks,portrait_checks=other['checks'],
 module_sha256=b.b.sha(OUT/'qol_bindings.dll'),scope='Actual native roof layer callback, 2/3 layer cycles, repeat/modifier/multiplayer gates, compiled key hook stack/owner forwarding, existing portrait regressions; native button/Windows APIs stubbed.',runtime_acceptance='pending user gameplay testing'))
print('Passed',checks+other['checks'],'roof/portrait checks')
