"""Execute compiled adapter against recreated owners, without launching game."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'modernization/build/remastered-1.1-port-preview'
source=(ROOT/'modernization/tools/verify_11_ui_elements.py').read_text()
prefix=source[:source.index('for battle in [False,True]:')]
prefix=prefix.replace("BUILD=ROOT/'modernization/build/remastered-1.1-ui-elements'","BUILD=ROOT/'modernization/build/remastered-1.1-port-preview'")
exec(prefix)
checks=0
for battle,port in [(False,True),(False,False),(True,False)]:
 for count in [234,95,61]:
  f=Fixture(battle,port)
  f.put(sym('port_icon_attempted'),1);f.put(sym('port_icon_file'),0x2008000)
  f.put(sym('sprite_draw_original'),0x2007010)
  for owner in [0x2003000,0x2004000,0x2003000]:
   data=owner+0x100;f.u.mem_write(data,b'SPR\0');f.put(data+12,count)
   f.put(owner,data,0,data+24,data+960,0,0,0,0,0,0x04000000)
   for frame in [0,1,2,43,54,73,99,100,107,233,234,-1]:
    control=0x2001000;f.put(control,0x5c77bc);f.put(control+0x11,1292,52,1386,156)
    f.put(control+0x55,owner);f.put(control+0x59,frame);f.calls=[]
    f.call(sym('port_icon_draw_hook'),ecx=control)
    selected=not battle and port and count==234 and 0<=frame<234
    assert f.calls==[sym('port_icon_sprite') if selected else owner]
    assert f.get(control+0x55)[0]==owner
    assert f.u.reg_read(UC_X86_REG_ESP)==0x20ff004
    if selected:
     assert f.get(sym('port_icon_sprite'),4)==(0x2008000,0,0x2008018,0x20083c0)
     assert f.get(sym('port_icon_sprite')+0x24)[0]==0x04000000
    checks+=1
report=dict(result='passed',checks=checks,module_sha256=hashlib.sha256((BUILD/'qol_bindings.dll').read_bytes()).hexdigest(),
 scope='compiled x86 repeated page recreation, all preview frame families, original owner restoration, battle/page/source exclusions and stack balance',
 runtime_acceptance='pending user testing; no gameplay launched')
(BUILD/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(report)
