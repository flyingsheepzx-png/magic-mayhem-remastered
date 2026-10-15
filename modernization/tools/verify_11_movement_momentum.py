"""Compiled native-gate continuity, startup/terrain/time and ABI tests. No game."""
import struct,json,pefile
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_11_movement_timing import setup
import build_11_movement_momentum as b
n,sym=setup(b.OUT);u=n.u;unit=0x1801000;typ=0x1803000;checks=0
def d(a):return struct.unpack('<i',u.mem_read(a,4))[0]
def field(off):return d(unit+off)
def initialize(action=2,speed=240,carry=37,threshold=192,kind=0,wait=0,direction=0,players=1,owner=0):
 u.mem_write(unit,b'\0'*0xe4b);u.mem_write(typ,b'\0'*0x100)
 for off,v in [(4,1),(0xe4,100),(0xac,typ),(0x5fc,action),(0x618,1),(0x610,kind),(0x66c,wait),(0x608,direction),(0xb63,speed),(0xb6b,carry),(0xb67,threshold),(0x174,owner)]:n.w(unit+off,v)
 n.w(typ+8,1);n.w(typ+0x10,10);n.w(typ+0x44,1);n.w(0x6e1f0c,players)
 n.call(sym('_mm_momentum_redirect_end'),[])
def capture():n.call(sym('momentum_capture'),[unit])
def apply(old_kind=0):return n.call(sym('momentum_continue'),[unit,old_kind])
def gate(old_kind=0):
 sp=0x20ff000;n.w(sp+0x1c,old_kind)
 u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ESI,unit);u.reg_write(UC_X86_REG_EBP,0)
 u.reg_write(UC_X86_REG_ECX,field(0x614));u.reg_write(UC_X86_REG_EDX,field(0x608))
 # Native resets common root offsets, then branches through compiled hook.
 u.mem_write(0x51143e,b'\xe9'+struct.pack('<i',sym('momentum_gate_hook')-0x511443)+b'\x90'*3)
 u.emu_start(0x511411,0x511471,count=100000)
 assert u.reg_read(UC_X86_REG_EIP)==0x511471 and u.reg_read(UC_X86_REG_ESP)==sp
def native_speed(previous,rise=0,nominal=240):
 sp=0x20ff000;out=0x1809000;target=out+4;n.w(out,previous)
 args=[4,0,1,0,rise,nominal,out,target]
 n.call(0x505920,args,typ)
 return d(out),d(target)
curves=[]
for owner in (0,1,3,7):
 for rate in (20,30,40):
  n.w(0x6de6fd,rate)
  for olddir in range(8):
   for turn in range(5):
    for redirect in (False,True):
     initialize(direction=olddir,owner=owner)
     if redirect:
      n.call(sym('_mm_momentum_redirect_begin'),[unit]);n.w(unit+0x618,0);n.w(unit+0x5fc,15)
     capture();n.call(sym('_mm_momentum_redirect_end'),[])
     n.w(unit+0x618,1);n.w(unit+0x614,olddir);n.w(unit+0x608,(olddir+turn)&7)
     n.w(unit+0xb63,300) # First native calculation must not double accelerate.
     before=bytes(u.mem_read(unit,0xe4b));gate()
     assert field(0xb63)==240 and field(0xb6b)==37
     after=bytearray(u.mem_read(unit,0xe4b));old=bytearray(before)
     for off in [0xb63,0xb4b,0xb47,0xb3f,0xb7f,0xb7b,0xb77]:after[off:off+4]=old[off:off+4]
     assert after==old
     current,desired=native_speed(field(0xb63));n.w(unit+0xb63,current)
     n.call(sym('momentum_turn_limit'),[unit,desired])
     assert field(0xb63)==(240 if turn<=1 else (180,150,120)[turn-2]);checks+=1
 # Startup is still actual native151,240 at nominal240/acceleration10.
 initialize(action=15,speed=0,owner=owner);capture();gate()
 assert field(0xb63)==0 and field(0xb6b)==0
 first,target=native_speed(0);second,_=native_speed(first)
 assert (first,second,target)==(151,240,240);checks+=1

for off,value in [(0x66c,5),(0x66c,7),(0x10c,1),(0x104,1),(4,0),(0xe4,0),(0x610,1),(0x618,0),(0xb63,0),(0xb63,-1),(0xb63,1000001),(0xb67,0),(0xb6b,-1),(0xb6b,192)]:
 initialize();n.w(unit+off,value);capture();before=bytes(u.mem_read(unit,0xe4b));assert apply()==0 and bytes(u.mem_read(unit,0xe4b))==before;checks+=1
for off in (0x71c,0x723):
 initialize();u.mem_write(unit+off,b'\1');capture();before=bytes(u.mem_read(unit,0xe4b));assert apply()==0 and bytes(u.mem_read(unit,0xe4b))==before;checks+=1
for kw in [dict(players=2),dict(action=1),dict(action=3),dict(action=15),dict(action=16),dict(kind=4)]:
 initialize(**kw);capture();before=bytes(u.mem_read(unit,0xe4b));assert apply()==0 and bytes(u.mem_read(unit,0xe4b))==before;checks+=1
# Never consume stale continuity on actual stop/wait; no owner privilege.
for action,wait in [(1,0),(15,0),(2,5),(2,7)]:
 initialize(action=action,wait=wait);n.call(sym('_mm_momentum_redirect_begin'),[unit]);n.w(unit+0x5fc,15);n.w(unit+0x66c,0);capture()
 assert apply()==0;checks+=1
# Kind change and duplicate application preserve native fallback.
initialize();capture();n.w(unit+0x610,1);assert apply(0)==0;checks+=1
initialize();capture();n.w(unit+0x5fc,3);assert apply()==0;checks+=1
initialize();capture();n.w(typ+0x44,2);assert apply()==0;checks+=1
initialize();capture();assert apply()==1;before=bytes(u.mem_read(unit,0xe4b));assert apply()==0 and bytes(u.mem_read(unit,0xe4b))==before;checks+=1
# Carry proportional to new animation threshold, no new root step generated.
for threshold in (96,192,288):
 initialize();capture();n.w(unit+0xb67,threshold);assert apply()==1
 assert field(0xb6b)==37*threshold//192< threshold;checks+=1
# Actual native acceleration with terrain target: slopes preserved, acute-turn
# speed respects new desired target and recovers by native acceleration later.
for rise in (-1,0,1):
 for turn in range(5):
  initialize();capture();n.w(unit+0x608,turn);assert apply()==1
  current,desired=native_speed(240,rise);n.w(unit+0xb63,current);n.call(sym('momentum_turn_limit'),[unit,desired])
  assert desired=={-1:360,0:240,1:160}[rise]
  if turn>1:assert field(0xb63)==desired*({2:6,3:5,4:4}[turn])//8
  curves.append(dict(rise=rise,turn=turn,desired=desired,first=field(0xb63),next=native_speed(field(0xb63),rise)[0]));checks+=1
# Naked entry hook stack/flags and exact overwritten prologue.
initialize();sp=0x20ff000;u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,unit)
for reg in (UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP):u.reg_write(reg,0x12345678)
u.reg_write(UC_X86_REG_EFLAGS,0x246);u.emu_start(sym('momentum_entry_hook'),0x510e86,count=10000)
assert u.reg_read(UC_X86_REG_ESP)==sp-0x3c and u.reg_read(UC_X86_REG_ECX)==unit
for reg in (UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP):assert u.reg_read(reg)==0x12345678
checks+=1
# Finish hook reads real native desired local[esp+2c], preserves flags/registers.
initialize();capture();n.w(unit+0x608,2);assert apply()==1
n.w(sp+0x2c,240);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ESI,unit);u.reg_write(UC_X86_REG_EFLAGS,0x246)
u.emu_start(sym('momentum_finish_hook'),0x511591,count=10000)
assert field(0xb63)==180 and u.reg_read(UC_X86_REG_ESP)==sp and u.reg_read(UC_X86_REG_EFLAGS)==0x246;checks+=1
# Native gate fallbacks keep native b73/direction rules, including multiplayer.
for players in (1,2):
 for action,carry,kind,turn in [(15,0,0,0),(15,1,0,0),(15,1,0,2),(15,1,1,0),(2,0,0,2)]:
  initialize(action=action,players=players,kind=kind);capture();n.w(unit+0xb73,carry);n.w(unit+0x614,0);n.w(unit+0x608,turn);gate(0)
  reset=action!=2 and (not carry or kind!=0 or turn>1)
  assert (field(0xb63)==0)==reset;checks+=1
# Controlled 12-root-step segments, actual native accumulator instructions and
# compiled compensated logic. These isolate cadence effects, not live routes.
travel=[]
for label,turns,redirects in [('straight',[0,0,0,0],False),('straight_replans',[0,0,0,0],True),('quarter_turns',[0,2,2,2],False),('half_turns',[0,4,4,4],False)]:
 for changed in (False,True):
  speed=0;remainder=0;direction=0;ticks=0
  n.w(sym('phases'),0);n.w(sym('phases')+4,0);u.mem_write(sym('original_walltime_trial'),b'\1');n.w(0x6de6fd,30)
  for seg,turn in enumerate(turns):
   initialize(action=15 if seg==0 else 2,speed=speed,carry=remainder,direction=direction)
   if redirects and seg:
    n.call(sym('_mm_momentum_redirect_begin'),[unit]);n.w(unit+0x5fc,15)
   capture();n.call(sym('_mm_momentum_redirect_end'),[])
   direction=(direction+turn)&7;n.w(unit+0x608,direction)
   if changed:
    if seg==0:n.w(unit+0xb63,0);n.w(unit+0xb6b,0)
    else:assert apply()==1
   else:
    # Original511411 preserves action2 even at a turn; explicit redirect15
    # with b73 clear restarts. Same-flat fast path avoids double acceleration.
    if seg==0 or redirects:n.w(unit+0xb63,0);n.w(unit+0xb6b,0)
   speed,desired=native_speed(field(0xb63));n.w(unit+0xb63,speed)
   if changed:n.call(sym('momentum_turn_limit'),[unit,desired]);speed=field(0xb63)
   steps=0
   while steps<12:
    contribution=n.call(sym('effective_speed'),[unit]);u.reg_write(UC_X86_REG_EBP,unit);u.reg_write(UC_X86_REG_EAX,contribution)
    u.emu_start(0x5104d7,0x5104f0,count=100)
    generated=u.reg_read(UC_X86_REG_EAX);steps+=generated;n.w(unit+0xb6b,field(0xb6b)-generated*192);ticks+=1
    assert ticks<1000
   remainder=field(0xb6b)
  travel.append(dict(scenario=label,policy='candidate' if changed else 'previous',ticks=ticks,nominal_seconds=ticks/30))
  checks+=1
assert next(r['ticks'] for r in travel if r['scenario']=='straight_replans' and r['policy']=='candidate')<next(r['ticks'] for r in travel if r['scenario']=='straight_replans' and r['policy']=='previous')
assert next(r['ticks'] for r in travel if r['scenario']=='quarter_turns' and r['policy']=='candidate')>next(r['ticks'] for r in travel if r['scenario']=='quarter_turns' and r['policy']=='previous')
# Compiled installer actually writes all three detours, validates all sites
# before mutating, and refuses an unknown signature. Windows calls are doubles.
for tamper in (False,True):
 q,qs=setup(b.OUT);pu=q.u;p=pefile.PE(str(b.OUT/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
 imports={i.name.decode():struct.unpack('<I',p.get_data(i.address-base,4))[0] for g in p.DIRECTORY_ENTRY_IMPORT for i in g.imports if i.name};p.close()
 for page in {v&~4095 for v in imports.values()}:pu.mem_map(page,4096)
 def api(machine,address,size,data):
  args={'VirtualProtect':4,'FlushInstructionCache':3,'GetCurrentProcess':0}
  for name,argc in args.items():
   if address!=imports[name]:continue
   sp=pu.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',pu.mem_read(sp,4))[0]
   if name=='VirtualProtect':q.w(struct.unpack('<I',pu.mem_read(sp+16,4))[0],4)
   pu.reg_write(UC_X86_REG_EAX,1);pu.reg_write(UC_X86_REG_ESP,sp+4+argc*4);pu.reg_write(UC_X86_REG_EIP,ret);break
 pu.hook_add(UC_HOOK_CODE,api)
 if tamper:pu.mem_write(0x51158b,b'\xcc')
 before=[bytes(pu.mem_read(a,sz)) for a,sz in [(0x510e80,6),(0x51143e,8),(0x51158b,6)]]
 result=q.call(qs('_mm_install_movement_momentum'),[])&255
 assert result==int(not tamper)
 if tamper:assert before==[bytes(pu.mem_read(a,sz)) for a,sz in [(0x510e80,6),(0x51143e,8),(0x51158b,6)]]
 else:
  for a,name in [(0x510e80,'momentum_entry_hook'),(0x51143e,'momentum_gate_hook'),(0x51158b,'momentum_finish_hook')]:
   blob=pu.mem_read(a,5);assert blob[0]==0xe9 and a+5+struct.unpack_from('<i',blob,1)[0]==qs(name)
 checks+=1
b.verify();report=dict(result='passed',module_sha256=b.b.sha(b.OUT/'repath.dll'),checks=checks,terrain_turn_curves=curves,
 scope='Compiled continuity/turn policy and native reset gate505920 acceleration, player/AI ownership20/30/40 rates, stop/wait/exclusions, proportional integer carry, naked x86 hooks, native multiplayer/b73 fallback. No live game; native safety/reservation code unchanged.',
 runtime_acceptance='pending user gameplay; travel/turn times can change, no claim of jitter cure')
report['synthetic_segment_cadence']=travel
previous=[]
for name,file in [('verify_11_roof_ghost.py','ghost-verification.json'),('verify_11_wrap_route.py','wrap-verification.json'),('verify_11_command_response.py','command-verification.json')]:
 p=b.OUT/file
 if p.exists():
  r=json.loads(p.read_text());assert r['module_sha256']==report['module_sha256'] and r['result']=='passed';previous.append(dict(fixture=name,checks=r['checks']))
# Dynamic regression's legacy output is overwritten by the authoritative report;
# recover only its verified same-module result from the preceding report.
p=b.OUT/'verification.json'
if p.exists():
 r=json.loads(p.read_text());
 if r.get('module_sha256')==report['module_sha256']:
  previous.extend(x for x in r.get('regressions',[]) if x['fixture']=='verify_11_dynamic_wait.py')
if len(previous)==4:report['regressions']=previous
b.base.write(b.OUT/'verification.json',report);print(json.dumps(report,indent=2))
