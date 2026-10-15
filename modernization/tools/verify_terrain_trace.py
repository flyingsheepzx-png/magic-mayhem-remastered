import sys,json,struct
from pathlib import Path
sys.path.insert(0,'modernization/tools')
from emulate_terrain_diagonal import Native
from install_terrain_trace import BUILD,DLL,sha,write
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_EIP
import pefile
p=pefile.PE(str(BUILD/'terrain_diagonal.dll'));base=p.OPTIONAL_HEADER.ImageBase
lines=(BUILD/'terrain.map').read_text().splitlines()
def sym(name):return int(next(x for x in lines if name in x).split()[2],16)
a,b=Native(),Native();a.patch(DLL);b.patch(BUILD/'terrain_diagonal.dll')
cases=0
for players in (1,2):
 for width in (1,2):
  for height in (1,2,4,6,8):
   a.w(0x6e1f0c,players);b.w(0x6e1f0c,players)
   a.set_profile(height,width);b.set_profile(height,width)
   for start,end in (((58,78,4),(57,77,4)),((54,74,5),(53,73,5)),((53,73,5),(54,74,5)),((54,74,5),(54,73,6))):
    assert a.edge(start,end)==b.edge(start,end);cases+=1
# Call only DllMain in isolated emulation, with module patching disabled.
for setting in ('','0','1','10'):
 n=Native();n.patch(BUILD/'terrain_diagonal.dll');u=n.u
 # Restore native signature before the DLL's attach-time check.
 u.mem_write(0x4f3fff,bytes.fromhex('837e04010f8588010000'))
 u.mem_map(0x3000000,4096)
 api=next(x.address for d in p.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name==b'GetEnvironmentVariableA')
 u.mem_write(api,struct.pack('<I',0x3000000))
 def env(uc,address,size,data):
  if address!=0x3000000:return
  sp=uc.reg_read(UC_X86_REG_ESP);ret,name,out,capacity=struct.unpack('<4I',uc.mem_read(sp,16))
  raw=bytes(uc.mem_read(name,64)).split(b'\0')[0]
  value=(setting if raw==b'MM_TERRAIN_DIAGONAL_TRACE' else '1').encode()
  uc.mem_write(out,value+b'\0');uc.reg_write(UC_X86_REG_EAX,len(value))
  uc.reg_write(UC_X86_REG_ESP,sp+16);uc.reg_write(UC_X86_REG_EIP,ret)
 u.hook_add(UC_HOOK_CODE,env)
 assert n.call(sym('_DllMain@12'),[base,1,0])==1
 assert bytes(u.mem_read(sym('?logging@@'),1))==bytes([setting=='1'])
write(BUILD/'verification.json',dict(terrain_cases=cases,trace_settings=4,result='passed',dll_sha256=sha(BUILD/'terrain_diagonal.dll'),gameplay_tested=False))
print((BUILD/'verification.json').read_text())
