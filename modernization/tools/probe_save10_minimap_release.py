"""Owned disposable formal-release save10 probe, background input/read-only RAM."""
import ctypes,json,time,shutil,struct
from pathlib import Path
import compare_remastered_ui_11 as c
from verify_hd60_runtime import read
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=c.ROOT;FORMAL=Path('D:/Games/Magic&Mayham_Remastered_1.1')

def expected(s,obj,x,y):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000);u.mem_map(0x2000000,0x100000)
 # Native reference uses logical width; leave its inverse/rotation/world math intact.
 u.mem_write(0x555ec0,read(s.k,s.handle,0x555ec0,0x160))
 u.mem_write(0x555f1d,bytes.fromhex('8babeb000000'))
 def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*[n&0xffffffff for n in v]))
 proxy=0x2001000
 for off,n in [(0xc5,1),(0x6159,4)]:put(proxy+off,*[s.i(obj+off+4*j) for j in range(n)])
 put(proxy+0xeb,1280)
 for a in [0x6c549c,0x6c5494,0x6c5498,0x689969,0x68996d,0x6903e8]:put(a,s.i(a))
 put(0x20ff000,0,1,x,y);u.reg_write(UC_X86_REG_ESP,0x20ff000);u.reg_write(UC_X86_REG_ECX,proxy)
 def skip(u,a,size,data):
  if a==0x555f74:u.reg_write(UC_X86_REG_EAX,1);u.reg_write(UC_X86_REG_EIP,0x555f77)
  if a==0x555f8f:
   u.reg_write(UC_X86_REG_ESP,u.reg_read(UC_X86_REG_ESP)+4);u.reg_write(UC_X86_REG_EIP,0x555f94)
 u.hook_add(UC_HOOK_CODE,skip);u.emu_start(0x555ec0,0x556020,count=500)
 return [u.reg_read(UC_X86_REG_ESI),u.reg_read(UC_X86_REG_EDI)]

def run(label,fixed=False):
 ctypes.windll.user32.SetProcessDPIAware()
 out=ROOT/'modernization/logs/remastered-ui'/label;out.mkdir(exist_ok=False)
 m=json.loads((FORMAL/'release-manifest.json').read_text(encoding='utf-8'))
 assert c.sha(FORMAL/'MagicMayhem-Remastered.exe')==m['launcher_sha256']
 assert c.sha(FORMAL/'runtime/Chaos-Wide169-engine.exe')==c.ENGINES['1.1']
 identity=dict(version='1.1',package=str(FORMAL),launcher_name='MagicMayhem-Remastered.exe',launcher_sha256=m['launcher_sha256'],engine_sha256=m['engine_sha256'])
 runtime=c.stage(identity,out/'package',FORMAL/'runtime/Save/10.sav')
 # Formal launcher deliberately clears the private input flag. Use its paired
 # diagnostic launcher with byte-identical embedded modules and formal assets.
 from install_11_minimap_v2 import resources
 binary=ROOT/('modernization/build/remastered-1.1-minimap-release/candidate.exe' if fixed else 'modernization/build/remastered-1.1-port-preview/candidate.exe')
 if not fixed:assert resources(binary)==resources(FORMAL/identity['launcher_name'])
 shutil.copy2(binary,runtime.parent/identity['launcher_name']);identity['launcher_sha256']=c.sha(binary)
 s=c.session_class()(identity,runtime,out/'run',75)
 with s:
  s.load_fixture('10')
  c.wait_control(s,lambda r:r['vtable']=='0x5c6f54')
  scanner=c.wait_control(s,lambda r:r['vtable']=='0x5c6a8c');assert len(scanner)==1
  obj=int(scanner[0]['pointer'],16);rect=scanner[0]['rect']
  s.result['click_hook_bytes']=read(s.k,s.handle,0x555f1d,6).hex()
  s.result['scanner']=dict(rect=rect,storage=s.i(obj+0xeb),rotation=s.i(obj+0xc5))
  rows=[]
  for dx,dy in [(0,0),(20,0),(-20,0),(0,15)]:
   x=(rect[0]+rect[2])//2+dx;y=(rect[1]+rect[3])//2+dy
   target=expected(s,obj,x,y);before=[s.i(0x689969),s.i(0x68996d)]
   s.click_base(x,y);time.sleep(.25);after=[s.i(0x689969),s.i(0x68996d)]
   rows.append(dict(click=[x,y],expected=target,before=before,after=after,match=target==after))
  s.result['minimap_clicks']=rows;s.shot('battle-save10',False)
  if fixed:assert all(r['match'] for r in rows),rows
 c.write_json(out/'result.json',s.result)
 print(json.dumps(dict(label=label,scanner=s.result['scanner'],clicks=rows),ensure_ascii=False))

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--fixed',action='store_true');a=p.parse_args();run(a.label,a.fixed)
