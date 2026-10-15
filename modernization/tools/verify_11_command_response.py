"""Compiled command adapters: native terrain, role parity, rollback and x86 ABI.

Action/segment-start helpers are explicit doubles for transaction tests; this
does not constitute runtime animation or combat acceptance.
"""
import json,struct,pefile
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import analyze_test18_corridor as a
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-command-response-v2'
P=pefile.PE(str(OUT/'repath.dll'));BASE=P.OPTIONAL_HEADER.ImageBase
LINES=(OUT/'repath.map').read_text().splitlines()
def sym(name):return int(next(x for x in LINES if '?'+name+'@@' in x).split()[2],16)
def val(n,off):return struct.unpack('<i',n.u.mem_read(n.unit+off,4))[0]
def setup():
 a.RUN=b.ROOT/'modernization/logs/remastered-ui/save3-route-before'
 n=a.Terrain();n.u.mem_map(BASE,(P.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(BASE,P.get_memory_mapped_image())
 n.w(0x6e1f0c,0);n.w(0x6def5c,2);n.w(0x644520,1)
 for off,v in [(4,1),(0xe4,100),(0x618,1),(0x5fc,2),(0x5ec,2),(0x5f0,3),(0x64c,1),(0x104,0),(0x10c,0),(0xa0,0),(0x784,0),(0xde3,0),(0xb6f,0),(0x174,1),(0x68,1),(0x6e8,0),(0x8f9,0)]:n.w(n.unit+off,v)
 n.u.mem_write(0x5120c0,b'\xc3')
 for off in [0x71c,0x723]:n.u.mem_write(n.unit+off,b'\0')
 for off,v in [(8,1),(12,4),(0x34,0),(0x44,1)]:n.w(n.typ+off,v)
 target=n.unit+0xe4b;n.u.mem_write(target,b'\0'*0xe4b)
 for off,v in [(0,1),(4,1),(0xe4,100),(8,29),(12,44),(16,5),(0x174,0)]:n.w(target+off,v)
 return n
def fake_redirect(n,success):
 calls=[]
 addr=sym('on_order_impl')
 n.u.mem_write(addr,b'\xb8'+struct.pack('<I',success)+b'\xc3')
 def capture(uc,address,size,user):
  if address==addr:calls.append(dict(task=val(n,0x5ec),pending=val(n,0x5f0),goal=[val(n,o) for o in (0x96b,0x96f,0x973)]))
 n.u.hook_add(UC_HOOK_CODE,capture)
 return calls
def main():
 checks=0;parity=[]
 for owner,selected in [(0,0),(1,1),(3,0),(7,1)]:
  for task in (2,3):
   n=setup();n.w(n.unit+0x174,owner);n.w(n.unit+0x68,selected);n.w(n.unit+0x5ec,task)
   calls=fake_redirect(n,1);world=n.u.mem_read(n.unit+20,12)
   n.call(sym('attack_response'),[n.unit],0,1000000)
   assert calls and calls[0]['task']==2
   assert val(n,0x5ec)==3 and val(n,0x5f0)==0 and val(n,0x5f4)==0x50afa0
   assert n.u.mem_read(n.unit+20,12)==world and val(n,0x64c)==1
   parity.append(calls[0]['goal']);checks+=1
 assert len({tuple(x) for x in parity})==1;checks+=1
 for owner,selected in [(0,0),(1,1),(3,0),(7,1)]:
  n=setup();n.w(n.unit+0x174,owner);n.w(n.unit+0x68,selected);n.w(n.unit+0x5ec,3);n.w(n.unit+0x5f0,2)
  calls=fake_redirect(n,1);n.call(sym('on_order'),[n.unit],0)
  assert calls and calls[0]['task']==2 and val(n,0x5ec)==2 and val(n,0x5f4)==0x510010 and val(n,0x5f0)==0;checks+=1
 for task in (2,3):
  n=setup();n.w(n.unit+0x5ec,task);calls=fake_redirect(n,0);before=bytes(n.u.mem_read(n.unit,0xe4b));cells=bytes(n.u.mem_read(0x1000000,12*80*80*30))
  n.call(sym('attack_response'),[n.unit],0,1000000)
  assert calls and bytes(n.u.mem_read(n.unit,0xe4b))==before and bytes(n.u.mem_read(0x1000000,len(cells)))==cells;checks+=1
 n=setup();n.w(n.unit+0x5ec,3);n.w(n.unit+0x5f0,2);fake_redirect(n,0);before=bytes(n.u.mem_read(n.unit,0xe4b));n.call(sym('on_order'),[n.unit],0);assert bytes(n.u.mem_read(n.unit,0xe4b))==before;checks+=1
 for offset,value,size in [(0x6e1f0c,1,4),(0x6e1f0c,2,4),(0x1801004,0,4),(0x18010e4,0,4),(0x1801618,0,4),(0x18015fc,15,4),(0x1801104,1,4),(0x180110c,1,4),(0x18010a0,1,4),(0x1801784,1,4),(0x1801de3,1,4),(0x180171c,1,1),(0x1801723,1,1),(0x1803008,2,4),(0x1803044,2,4),(0x1803034,1,4),(0x18015ec,14,4),(0x18015f0,8,4),(0x180164c,-1,4)]:
  n=setup();n.u.mem_write(offset,(value&((1<<(size*8))-1)).to_bytes(size,'little'));calls=fake_redirect(n,1);before=bytes(n.u.mem_read(n.unit,0xe4b));n.call(sym('attack_response'),[n.unit],0,1000000)
  assert not calls and bytes(n.u.mem_read(n.unit,0xe4b))==before;checks+=1
 # Existing/queued movement effects removed once, other task effects preserved.
 for task in (2,3):
  for selected in (0,1):
   n=setup();n.w(n.unit+0x68,selected)
   if task==2:n.w(n.unit+0x5ec,3);n.w(n.unit+0x5f0,2)
   fake_redirect(n,1);n.u.mem_write(0x4943f0,b'\xc3')
   tree=0x1808000;head=tree+32;node1=tree+80;node2=tree+144
   n.w(n.unit+0x6e8,0x1809000);n.w(n.unit+0x8f9,tree)
   for addr,value in [(tree+8,2),(tree+4,head),(head,node1),(node1,node2),(node2,head),(node1+8,2),(node1+40,0x1809100),(node2+8,3),(node2+40,0x1809200)]:n.w(addr,value)
   deleted=[];refresh=[]
   def observe(uc,address,size,user):
    if address==0x4943f0:deleted.append(uc.reg_read(UC_X86_REG_ECX))
    if address==0x5120c0:refresh.append((val(n,0x5ec),val(n,0x5f0),val(n,0x6e8)))
   n.u.hook_add(UC_HOOK_CODE,observe)
   entry='attack_response' if task==3 else 'on_order'
   n.call(sym(entry),[n.unit],0,1000000)
   assert deleted==[0x1809000,0x1809100] and val(n,0x6e8)==0
   assert struct.unpack('<I',n.u.mem_read(node1+40,4))[0]==0 and struct.unpack('<I',n.u.mem_read(node2+40,4))[0]==0x1809200
   assert refresh==([(task,0,0)] if selected else []);checks+=1
 # Rejected physical redirect must preserve marker without deletion/refresh.
 n=setup();fake_redirect(n,0);n.w(n.unit+0x6e8,0x1809000);before=bytes(n.u.mem_read(n.unit,0xe4b));n.call(sym('attack_response'),[n.unit],0,1000000);assert bytes(n.u.mem_read(n.unit,0xe4b))==before;checks+=1
 # Execute naked replacement with native50aa30; rejected width avoids planner.
 n=setup();n.w(n.typ+8,2);u=n.u;sp=0x20ff000
 u.mem_write(sp,struct.pack('<6I',3,0,0,0,0x5392ef,0));u.reg_write(UC_X86_REG_ESP,sp)
 u.reg_write(UC_X86_REG_ECX,n.unit);u.reg_write(UC_X86_REG_ESI,n.unit)
 u.emu_start(sym('attack_response_hook'),0x50aef7,count=1000000)
 assert u.reg_read(UC_X86_REG_EIP)==0x50aef7 and u.reg_read(UC_X86_REG_ESP)==sp+4 and val(n,0x5f0)==3;checks+=1
 # Actual redirect planning/sweep/transaction body. Startup helpers are doubles;
 # check physical position, successful commit and forced native-start rollback.
 for succeeds in (0,1):
  n=setup();n.w(n.unit+0x5f0,2);n.w(n.unit+0xb6f,1)
  for off,v in zip((0x96b,0x96f,0x973),(28,45,5)):n.w(n.unit+off,v)
  n.u.mem_write(0x50db60,b'\xc2\x04\x00');n.u.mem_write(0x510e80,b'\xc3');n.u.mem_write(0x5093e0,b'\xc2\x0c\x00')
  def start(uc,address,size,user):
   if address==0x510e80:n.w(n.unit+0x618,succeeds);n.w(n.unit+0xb5f,val(n,0x1c));n.w(n.unit+0xb57,0)
  n.u.hook_add(UC_HOOK_CODE,start)
  before=bytes(n.u.mem_read(n.unit,0xe4b));world=bytes(n.u.mem_read(n.unit+20,12));cells=bytes(n.u.mem_read(0x1000000,12*80*80*30))
  result=n.call(sym('on_order_impl'),[n.unit,0,1],0,10000000)&255
  assert result==succeeds,(succeeds,result)
  assert bytes(n.u.mem_read(n.unit+20,12))==world and bytes(n.u.mem_read(0x1000000,len(cells)))==cells
  if not succeeds:assert bytes(n.u.mem_read(n.unit,0xe4b))==before
  checks+=1
 report=dict(result='passed',checks=checks,module_sha256=b.sha(OUT/'repath.dll'),army_parity=True,world_continuity=True,rollback=True,native_terrain_validators=True,explicit_doubles='on_order_impl for adapter plumbing; action15/start/release for redirect transaction fixture. Real startup occupancy/animation and combat performance require user acceptance.',runtime_acceptance='pending user save18 testing')
 (OUT/'command-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
