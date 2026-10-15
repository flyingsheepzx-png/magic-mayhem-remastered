"""Execute compiled portrait detour plus native command construction in Unicorn."""
import struct,pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-teammate-portrait'
engine=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
assert b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
e=pefile.PE(str(engine));p=pefile.PE(str(OUT/'qol_bindings.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(OUT/'qol_bindings.map').read_text().splitlines()
def sym(name):return int(next(x for x in lines if '?'+name+'@' in x).split()[2],16)
hook=sym('teammate_mouse_hook');readable=sym('readable')
stack=0x20ff000;end=0x20fe000;units=0x2100000;caster=units;target=units+0xe4b;control=0x2200000
def case(flags,mode=2,players=1,pending=0,valid=5,target_kind='alive',patched=True):
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for a,n in [(0x400000,0x400000),(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095),(0x2000000,0x300000)]:u.mem_map(a,n)
 u.mem_write(0x400000,e.get_memory_mapped_image());u.mem_write(base,p.get_memory_mapped_image())
 def w(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
 def d(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 assert u.mem_read(0x463030,10)==bytes.fromhex('8a44240481ec00020000')
 entry=0x463030
 if patched:u.mem_write(entry,b'\xe9'+struct.pack('<i',hook-entry-5)+b'\x90'*5)
 w(0x6e1f0c,players);w(0x6903e8,mode);w(0x6a2dd0+0x18ec,caster);w(0x6def58,units);w(0x6def5c,3)
 w(caster,77);w(caster+0x5e8,pending);w(caster+0x570,41);w(target,123);w(target+4,1);w(target+0xe4,549)
 w(control+0x89,0 if target_kind=='null' else target+1 if target_kind=='misaligned' else target)
 if target_kind=='dead':w(target+0xe4,0)
 if target_kind=='inactive':w(target+4,0)
 w(0x5e04c8,16);w(0x6df180,0);w(0x68999d,0)
 w(stack,end,flags,*([0]*10));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,control)
 keep=[UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
 for i,r in enumerate(keep):u.reg_write(r,0x123400+i)
 events=[];payloads=[]
 def ret(argc,value=0):
  sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_EIP,d(sp));u.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
 def trace(u,a,size,data):
  sp=u.reg_read(UC_X86_REG_ESP);ecx=u.reg_read(UC_X86_REG_ECX)
  if a==readable:ret(0,1)
  elif a==0x57cf40:events.append(('predicate',ecx));ret(0,valid)
  elif a==0x57ce70:events.append(('cast',ecx,d(0x5e04c8))) # Execute actual native constructor.
  elif a==0x466870:ret(1,caster)
  elif a==0x533fa0:
   ptr=d(sp+4);payloads.append(list(struct.unpack('<9I',u.mem_read(ptr,36))));ret(1)
  elif a==0x537bd0:events.append(('queue',ecx));ret(1)
  elif a==0x509bd0:events.append(('cancel',ecx,d(sp+4)));w(ecx+0x5e8,-1);ret(1)
  elif a==0x4f7ae0:events.append(('select',d(sp+4)));ret(1)
  elif a==0x5073d0:events.append(('select-unit',ecx));ret(0)
  elif a==0x56f000:events.append(('error-sound',));ret(7)
 u.hook_add(UC_HOOK_CODE,trace)
 try:u.emu_start(entry,end,count=10000)
 except Exception:
  print('failed',flags,hex(u.reg_read(UC_X86_REG_EIP)),hex(u.reg_read(UC_X86_REG_ESP)),events);raise
 assert u.reg_read(UC_X86_REG_EIP)==end and u.reg_read(UC_X86_REG_ESP)==stack+48
 assert all(u.reg_read(r)==0x123400+i for i,r in enumerate(keep))
 assert d(0x5e04c8)==16
 return events,payloads,d(caster+0x5e8)

checks=0
# A held/down button never casts; release uses target123, caster77, Cure41.
for flags in [1,2,4,8,0x22]:
 events,payload,pending=case(flags)
 if flags&12:
  assert not payload and not any(e[0] in ['cast','select','select-unit'] for e in events)
  assert (pending==0 if flags==4 else pending==0xffffffff)
 elif flags&2:
  assert events==[('predicate',target),('cast',target,5),('queue',0x6a2898)]
  assert len(payload)==1 and (payload[0][0],payload[0][7],payload[0][8])==(41,77,123)
 else:assert not events and not payload
 checks+=1
for kind in ['null','misaligned','dead','inactive']:
 events,payload,_=case(2,target_kind=kind);assert not events and not payload;checks+=1
events,payload,_=case(2,valid=16);assert events==[('predicate',target)] and not payload;checks+=1
# Outside targeting/multiplayer/no pending spell, exact native behavior remains.
for kwargs in [dict(mode=0),dict(mode=1),dict(players=2),dict(pending=-1),dict(pending=30)]:
 for flags in [0,1,2,4,8,0x40]:
  assert case(flags,**kwargs)==case(flags,patched=False,**kwargs);checks+=1
# Old right release submits a native portrait command; old left selects instead.
left=case(2,patched=False);assert not left[1] and ('select',target) in left[0];checks+=1
# Cursor16 deliberately rejects native old right cast; it still enters submitter.
right=case(8,patched=False);assert ('cast',target,16) in right[0];checks+=1
b.write(OUT/'verification.json',dict(result='passed',checks=checks,module_sha256=b.sha(OUT/'qol_bindings.dll'),scope='Compiled detour/native teammate callback ABI; release-only target123/caster77/Cure41 native command payload; invalid targets, selection preservation, right cancellation, native non-targeting fallback. Native eligibility/queue APIs stubbed; battle acceptance pending user.'))
print('Passed',checks,'compiled/native portrait checks')
