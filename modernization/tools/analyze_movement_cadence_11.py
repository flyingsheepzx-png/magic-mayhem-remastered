"""Read-only installed identity + execute native acceleration/cadence in emulator.

No game launch, configuration write, or runtime patch. Synthetic speed inputs
demonstrate the native mechanics; they are not live protagonist timings.
"""
import json,struct
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_ESI
import build_11_port_bindings_hd as b
from install_11_minimap_v2 import resources

engine=b.base.DEST/'runtime/Chaos-Wide169-engine.exe'
expected='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
assert b.b.sha(engine)==expected
for e,m,k in b.base.targets():
 j=json.loads(m.read_text(encoding='utf-8'));assert b.b.sha(e)==j['launcher_sha256']
 assert resources(e)==resources(b.OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
pe=pefile.PE(str(engine));u=Uc(UC_ARCH_X86,UC_MODE_32)
u.mem_map(0x400000,0x400000);u.mem_write(0x400000,pe.get_memory_mapped_image())
u.mem_map(0x2000000,0x300000)
def w(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
def d(a):return struct.unpack('<i',u.mem_read(a,4))[0]
stack=0x20ff000;end=0x20fe000;typeptr=0x2100000;speedptr=0x2110000;targetptr=speedptr+4

def speed(acceleration=10,previous=0,rise=0,move_kind=0,nominal=240):
 w(typeptr+0x10,acceleration);w(speedptr,previous,0)
 # Eight actual thiscall parameters: terrain divisor, move kind, delta X/Y/Z,
 # animation-distance threshold, current speed pointer, desired-speed output.
 w(stack,end,4,move_kind,1,0,rise,nominal,speedptr,targetptr)
 u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,typeptr)
 u.emu_start(0x505920,end,count=10000)
 assert u.reg_read(UC_X86_REG_ESP)==stack+36
 return dict(previous=previous,current=d(speedptr),target=d(targetptr))

curves={}
for rise in (-1,0,1):
 previous=0;rows=[]
 for segment in range(8):
  result=speed(previous=previous,rise=rise);rows.append(result);previous=result['current']
 curves[str(rise)]=rows
assert curves['0'][0]['current']<curves['0'][0]['target']
assert curves['0'][-1]['current']==curves['0'][-1]['target']
assert curves['1'][0]['target']<curves['0'][0]['target']<curves['-1'][0]['target']
for rise in (-1,1):assert speed(rise=rise,move_kind=4)['target']==speed(move_kind=4)['target']

# Actual native movement accumulator instructions, stop before animation calls.
def cadence(rate,threshold,ticks=20,compensate=False):
 unit=0x2120000;w(unit+0xb63,rate);w(unit+0xb67,threshold);w(unit+0xb6b,0)
 from unicorn.x86_const import UC_X86_REG_EBP
 rows=[];fraction=0
 for tick in range(ticks):
  u.reg_write(UC_X86_REG_EBP,unit);w(stack);u.reg_write(UC_X86_REG_ESP,stack)
  if compensate:
   numerator=rate*31+fraction;fraction=numerator%50;u.reg_write(UC_X86_REG_EAX,numerator//50)
   u.emu_start(0x5104d7,0x5104f0,count=100)
  else:u.emu_start(0x5104d1,0x5104f0,count=100)
  steps=u.reg_read(UC_X86_REG_EAX);remainder=d(unit+0xb6b)-steps*threshold;w(unit+0xb6b,remainder)
  rows.append(dict(tick=tick+1,steps=steps,remainder=remainder))
 return rows
cadences={str(rate):cadence(rate,192,compensate=True) for rate in (60,120,192,240)}
assert any(r['steps']==0 for r in cadences['120'])

# Actual native segment-start reset gate. Direction helper is a controlled
# double; all branch conditions and writes use installed engine bytes.
turn_difference=0
def trace(machine,address,size,data):
 if address==0x4ead10:
  sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EAX,turn_difference)
  u.reg_write(UC_X86_REG_ESP,sp+4);u.reg_write(UC_X86_REG_ECX,0x2120000)
  from unicorn.x86_const import UC_X86_REG_EIP
  u.reg_write(UC_X86_REG_EIP,d(sp))
hook=u.hook_add(UC_HOOK_CODE,trace);reset_cases=[]
for action,carry,mode_same,turn in [(2,0,True,2),(15,0,True,0),(15,1,True,0),(15,1,True,2),(15,1,False,0)]:
 turn_difference=turn;unit=0x2120000;w(unit+0x5fc,action);w(unit+0xb73,carry);w(unit+0x610,0 if mode_same else 1)
 w(unit+0xb63,240);w(unit+0xb6b,37);w(stack+0x1c,0)
 u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ESI,unit);u.reg_write(UC_X86_REG_EBP,0)
 u.reg_write(UC_X86_REG_ECX,unit);u.emu_start(0x511411,0x511471,count=1000)
 resets=d(unit+0xb63)==0;assert resets==(action!=2 and (not carry or not mode_same or turn>1))
 reset_cases.append(dict(action=action,carry=carry,mode_same=mode_same,turn=turn,reset=resets))
u.hook_del(hook)
report=dict(result='passed',engine_sha256=expected,scope='Installed manifests/resources checked. Actual engine505920,4eaca0,4eac10,59bee0 acceleration arithmetic and5104d1 accumulator executed in Unicorn. Synthetic terrain-divisor4,nominal240/type-acceleration10 inputs; cadence emulates installed31/50 contribution. No live gameplay or wall-clock/frame acceptance.',native_acceleration_curves=curves,cadence=cadences,
 native_reset_cases=reset_cases,
 render_prediction_to_actual_contribution_ratio=50/31,
 functions={hex(a):dict(bytes=pe.get_data(a-0x400000,n).hex()) for a,n in [(0x505920,16),(0x5104d1,12),(0x51143d,15)]})
out=b.b.ROOT/'modernization/logs/movement-cadence-11';out.mkdir(exist_ok=True)
b.base.write(out/'native-analysis.json',report)
print(json.dumps(dict(result='passed',flat_speed_sequence=[r['current'] for r in curves['0'][:3]],slope_targets={k:v[0]['target'] for k,v in curves.items()},reset_cases=reset_cases),indent=2));pe.close()
