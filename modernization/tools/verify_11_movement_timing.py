"""Offline compiled x86 logic equivalence and render-reader verification.
No game launch; synthetic units are not live jitter acceptance.
"""
import json,struct,subprocess,math,os
import pefile
from unicorn.x86_const import *
from emulate_11_render import Native
import build_11_movement_timing as b
if os.environ.get('MM_MOVEMENT_VERIFY_MOMENTUM'):
 import build_11_movement_momentum as b

def setup(out):
 n=Native();p=pefile.PE(str(out/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
 n.u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(base,p.get_memory_mapped_image());p.close()
 lines=(out/'repath.map').read_text().splitlines()
 def sym(name):
  return int(next(x for x in lines if ('?'+name+'@@' in x if not name.startswith('_') else name+' ' in x)).split()[2],16)
 return n,sym

def main():
 b.verify();out=b.OUT
 (out/'timing_test.cmd').write_text('''@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
cl /nologo /O2 /EHsc /std:c++17 /I. "../../tests/movement_timing_test.cpp" /link /OUT:movement_timing_test.exe
if errorlevel 1 exit /b 1
movement_timing_test.exe
''')
 subprocess.run(['cmd','/c','timing_test.cmd'],cwd=out,check=True)
 old,osym=setup(b.SOURCE);new,nsym=setup(out);checks=0;unit=0x1801000
 for n in (old,new):n.u.mem_write(unit,b'\0'*0xe4b)
 for walltime in (0,1):
  for rate in (20,30,40):
   for players in (0,1,2):
    for id in (0,7,4095,4096):
     for n,sym in ((old,osym),(new,nsym)):
      n.w(0x6de6fd,rate);n.w(0x6e1f0c,players);n.u.mem_write(sym('original_walltime_trial'),bytes([walltime]));n.u.mem_write(unit,struct.pack('<H',id))
     for tick in range(70):
      speed=(151,240,160,360,1,1000000,0,-1,1000001)[tick%9]
      for n in (old,new):n.w(unit+0xb63,speed)
      carry=bytes(new.u.mem_read(nsym('phases'),4096*8));before=bytes(new.u.mem_read(unit,0xe4b))
      prediction=new.call(nsym('_mm_movement_prediction_contribution'),[unit])
      assert prediction==new.call(nsym('_mm_movement_prediction_contribution'),[unit])
      assert bytes(new.u.mem_read(nsym('phases'),4096*8))==carry and bytes(new.u.mem_read(unit,0xe4b))==before
      for n,sym in ((old,osym),(new,nsym)):
       for reg in (UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP):n.u.reg_write(reg,0x12345678)
      a=old.call(osym('effective_speed'),[unit]);z=new.call(nsym('effective_speed'),[unit])
      assert a==z==prediction
      for n in (old,new):
       assert n.u.reg_read(UC_X86_REG_ESP)==0x20ff004
       for reg in (UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP):assert n.u.reg_read(reg)==0x12345678
      assert bytes(old.u.mem_read(osym('phases'),4096*8))==bytes(new.u.mem_read(nsym('phases'),4096*8))
      # Native accumulator itself remains unchanged, including quotient/carry.
      for n in (old,new):
       n.w(unit+0xb67,192);n.w(unit+0xb6b,tick%192);n.u.reg_write(UC_X86_REG_EBP,unit);n.u.reg_write(UC_X86_REG_EAX,z)
       n.u.emu_start(0x5104d7,0x5104f0,count=100)
      assert old.u.reg_read(UC_X86_REG_EAX)==new.u.reg_read(UC_X86_REG_EAX)
      assert bytes(old.u.mem_read(unit,0xe4b))==bytes(new.u.mem_read(unit,0xe4b));checks+=1
 # Pointer reuse: reader must use zero carry without installing/resetting it.
 for n,sym in ((old,osym),(new,nsym)):
  n.w(0x6de6fd,30);n.w(0x6e1f0c,0);n.u.mem_write(sym('original_walltime_trial'),b'\1')
  n.u.mem_write(unit,struct.pack('<H',7));n.w(unit+0xb63,151);n.call(sym('effective_speed'),[unit])
 other=unit+0x2000;new.u.mem_write(other,bytes(new.u.mem_read(unit,0xe4b)));before=bytes(new.u.mem_read(nsym('phases'),32768))
 assert new.call(nsym('_mm_movement_prediction_contribution'),[other])==151*31//50
 assert bytes(new.u.mem_read(nsym('phases'),32768))==before;checks+=1
 # Compiled renderer projection with fractional carry, endpoints, slopes,
 # redirected step geometry and all four camera rotations. Writes only outputs.
 new.w(nsym('___isa_available'),2) # Emulate normal SSE4.1 CRT initialization.
 for continuous in (0,1):
  new.u.mem_write(nsym('continuous_enabled'),bytes([continuous]))
  for rotation in range(4):
   new.w(nsym('rotation'),rotation)
   for rise in (-15,0,15):
    for elapsed in (0,.3,.75):
     for maxphase in (.4,2):
      actor=0x1808000;x=actor+128;y=x+4
      phase=.2;speed=149/192;stepx=7.;stepy=-3.;steph=12.;fracx=.5;fracy=-.25
      blob=struct.pack('<I7i8d',unit,0,0,0,4,2,1,rise,phase,speed,stepx,stepy,steph,fracx,fracy,maxphase)
      new.u.mem_write(actor,blob);parts=struct.unpack('<2I',struct.pack('<d',elapsed))
      new.call(nsym('projected_shift'),[actor,*parts,x,y])
      assert bytes(new.u.mem_read(actor,len(blob)))==blob
      if continuous:
       p=min(phase+speed*elapsed,maxphase);wx=fracx+stepx*p;wy=fracy+stepy*p;h=max(-16-rise,min(16-rise,steph*p))
      else:wx=4*elapsed;wy=2*elapsed;h=elapsed
      sx,sy=((wx-wy,(wx+wy)*.5),(wx+wy,(wy-wx)*.5),(wy-wx,-(wx+wy)*.5),(-wx-wy,(wx-wy)*.5))[rotation]
      assert struct.unpack('<2i',new.u.mem_read(x,8))==(math.floor(sx+.5),math.floor(sy-h+.5));checks+=1
 report=dict(result='passed',module_sha256=b.b.sha(out/'repath.dll'),compiled_cases=checks,
  tests='Shared C++ integer conservation/tick conversion; previous/new compiled logic exact equality and x86 ABI; repeated render-reader state immutability; native accumulator; pointer reuse; compiled render projection rotations/slope/endpoint/redirect geometry.',
  policy='Preserves installed 30Hz 31/50 (probe 2/3), other rates raw native contribution and multiplayer fallback. Continuous replay uses selected tick interval; existing 30Hz-only replay eligibility unchanged.',
  runtime_acceptance='pending user testing; visible jitter causality unproven')
 b.base.write(out/('timing-preservation.json' if os.environ.get('MM_MOVEMENT_VERIFY_MOMENTUM') else 'verification.json'),report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
