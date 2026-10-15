"""User-authorized owned save10 HD HUD/minimap probe; isolated player data."""
import ctypes,json,shutil,time
import numpy as np
from PIL import Image
from pathlib import Path
import compare_remastered_ui_11 as c
from probe_save10_minimap_release import expected,FORMAL
from install_11_minimap_v2 import resources
from build_11_battle_hud import OUT,ASSET
from build_11_surface_lifecycle import idle

def run():
 idle();ctypes.windll.user32.SetProcessDPIAware()
 out=c.ROOT/'modernization/logs/remastered-ui'/('save10-battle-hud-'+str(time.time_ns()));out.mkdir()
 m=json.loads((FORMAL/'release-manifest.json').read_text(encoding='utf-8'))
 assert c.sha(FORMAL/'MagicMayhem-Remastered.exe')==m['launcher_sha256']
 identity=dict(version='1.1',package=str(FORMAL),launcher_name='MagicMayhem-Remastered.exe',launcher_sha256=m['launcher_sha256'],engine_sha256=m['engine_sha256'])
 runtime=c.stage(identity,out/'package',FORMAL/'runtime/Save/10.sav')
 binary=c.ROOT/'modernization/build/remastered-1.1-minimap-release/candidate.exe'
 assert resources(binary)==resources(FORMAL/identity['launcher_name'])
 shutil.copy2(binary,runtime.parent/identity['launcher_name']);identity['launcher_sha256']=c.sha(binary)
 dll=OUT/'wrapper/bin/Release/ddraw.dll'
 assert c.sha(dll)==json.loads((OUT/'verification.json').read_text())['wrapper_sha256']
 shutil.copy2(dll,runtime/'ddraw.dll');shutil.copy2(ASSET/'battle-hud.bin',runtime/'Sprites/battle-hud.bin')
 s=c.session_class()(identity,runtime,out/'run',75)
 with s:
  s.load_fixture('10');c.wait_control(s,lambda r:r['vtable']=='0x5c6f54')
  s.shot('battle-hud',False)
  assert s.records['battle-hud']['font_heights']==[32,22,15]
  scanner=c.wait_control(s,lambda r:r['vtable']=='0x5c6a8c');assert len(scanner)==1
  obj=int(scanner[0]['pointer'],16);rect=scanner[0]['rect'];rows=[]
  for dx,dy in [(0,0),(20,0),(-20,0),(0,15)]:
   x=(rect[0]+rect[2])//2+dx;y=(rect[1]+rect[3])//2+dy
   target=expected(s,obj,x,y);s.click_base(x,y);time.sleep(.25)
   actual=[s.i(0x689969),s.i(0x68996d)];rows.append(dict(click=[x,y],expected=target,actual=actual));assert target==actual
  s.result['checks']['minimap']=rows;s.result['hud_wrapper_sha256']=c.sha(dll)
  s.shot('battle-hud-after-minimap',False)
 assert s.result['restored'] and not s.result['cleanup_errors']
 image=np.asarray(Image.open(s.records['battle-hud']['native']).convert('RGB'))
 assert image.shape==(1440,2560,3)
 details={}
 for name,box in [('main',(2340,1200,2490,1380)),('team',(12,154,132,374)),('spell',(2210,1320,2330,1438))]:
  x1,y1,x2,y2=box;a=image[y1:y2,x1:x2]
  details[name]=int(np.any(a[::2,::2]!=a[1::2,1::2],axis=2).sum());assert details[name]>100
 c.write_json(OUT/'runtime-verification.json',dict(result='passed',report=str(out/'run/capture.json'),wrapper_sha256=c.sha(dll),pack_sha256=c.sha(ASSET/'battle-hud.bin'),minimap=rows,detail_pixels=details,fonts=[32,22,15],restored=True,user_acceptance='pending'))
 c.write_json(out/'result.json',s.result);print(out)

if __name__=='__main__':run()
