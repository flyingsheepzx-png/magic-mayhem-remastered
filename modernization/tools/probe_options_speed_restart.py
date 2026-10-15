"""Actual battle logic-boundary counts after native options confirmation."""
import ctypes,time,shutil,re,json,pefile
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
import prepare_options_speed as prep
from install_11_minimap_v2 import resources
ctypes.windll.user32.SetProcessDPIAware();p=prep.base.DEST
identity=dict(version='1.1',package=str(p),launcher_name=prep.base.ENTRY,launcher_sha256=c.sha(p/prep.base.ENTRY),engine_sha256=c.ENGINES['1.1'])
out=prep.b.ROOT/'modernization/logs/remastered-ui/options-speed-acceptance-v2'
rt=out/'package/runtime';candidate=prep.OUT/'candidate.exe';identity['launcher_sha256']=c.sha(candidate)
prefs=rt/'CFG/prefs.cfg';rows=json.loads((out/'measurements.json').read_text())
for fps in [40,30,20]:
 prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec='+str(fps).encode(),prefs.read_bytes()))
 s=c.session_class()(identity,rt,out/('restart-'+str(fps)),65);s.expected_logic=fps
 with s:
  assert s.i(0x6de6fd)==fps
  s.click_base(640,576);time.sleep(.35);s.shot('restored-speed',False)
  from PIL import Image
  image=Image.open(s.run/'restored-speed-2560x1440.png')
  dots=[image.getpixel((1538,y)) for y in [390,450,510]]
  assert max(dots[[40,30,20].index(fps)])>90
  assert all(max(dot)<30 for n,dot in enumerate(dots) if n!=[40,30,20].index(fps))
  print('restored',fps,dots,flush=True)
c.write_json(prep.OUT/'runtime-acceptance.json',dict(result='passed',candidate_sha256=c.sha(candidate),logic_rates=rows,restart_radio_all_rates=True,evidence=str(out)))
