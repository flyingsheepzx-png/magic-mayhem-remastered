import ctypes,time,shutil,json,re
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as base
import build_remastered_11 as b
from install_11_minimap_v2 import resources
ctypes.windll.user32.SetProcessDPIAware()
p=base.DEST
identity=dict(version='1.1',package=str(p),launcher_name=base.ENTRY,launcher_sha256=c.sha(p/base.ENTRY),engine_sha256=c.ENGINES['1.1'])
out=b.ROOT/'modernization/logs/remastered-ui/options-resolution-acceptance-v3';out.mkdir(exist_ok=False)
rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav')
candidate=b.ROOT/'modernization/build/remastered-1.1-options-resolution-v3/candidate.exe'
assert all(resources(candidate)[i]==resources(p/base.ENTRY)[i] for i in [101,103])
shutil.copy2(candidate.parent/'wrapper/bin/Release/ddraw.dll',rt/'ddraw.dll')
shutil.copy2(candidate,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
s=c.session_class()(identity,rt,out/'run',100)
rows=[]
def record(label):
 r=W.RECT();hw=s.window();s.u.GetClientRect(hw,ctypes.byref(r))
 row=dict(label=label,hwnd=hw,native_hwnd=s.i(0x657c84),client=[r.right,r.bottom],ini=(rt/'remastered-settings.ini').read_text(),controls=s.controls())
 rows.append(row);print(label,row['client'],'hwnds',hw,row['native_hwnd'],flush=True);c.write_json(out/'measurements.json',rows)
with s:
 record('startup');s.click_base(640,576);time.sleep(.6);record('options');s.shot('options',False)
 for high in [True,False]:
  s.click_base(290,339 if high else 369);s.shot("selected-"+str(high),False);s.click_base(352,660);time.sleep(1);record('applied-'+str(high));assert rows[-1]['client']==([2560,1440] if high else [1920,1080])
  s.click_base(640,576);time.sleep(.4)
 msg=s.u.RegisterWindowMessageW('MagicMayhem.Remastered.Display.v1');ack=ctypes.c_size_t()
 ok=s.u.SendMessageTimeoutW(s.window(),msg,1920,1080,2,4000,ctypes.byref(ack));print('direct message',ok,ack.value,flush=True)
 time.sleep(.4);record('direct-1920')
 s.click_base(938,660);time.sleep(.4);s.load_fixture('14');time.sleep(.5);record('battle-1920');s.shot('battle-1920',False)
 assert rows[-1]['client']==[1920,1080]
 assert any(r['vtable']=='0x5c6f54' for r in s.controls())
 assert [s.i(0x6a49f0),s.i(0x6a49f4)]==[2560,1440]

for width in [2560,1920]:
 (rt/'remastered-settings.ini').write_text('[display]\nresolution='+str(width)+'x'+str(width*9//16)+'\n')
 s=c.session_class()(identity,rt,out/('restart-'+str(width)),90)
 with s:
  record('restart-'+str(width));assert rows[-1]['client']==[width,width*9//16]
  s.click_base(640,576);time.sleep(.4);s.shot('restored-option',False)
  radios=[r for r in s.controls() if r['rect'] in [[560,648,1280,708],[560,708,1280,768]]]
  c.write_json(out/('radio-'+str(width)+'.json'),[{**r,'memory':__import__('verify_hd60_runtime').read(s.k,s.handle,int(r['pointer'],16),126).hex()} for r in radios])
  s.click_base(938,660);time.sleep(.4);s.load_fixture('14');time.sleep(.5);record('battle-'+str(width));s.shot('battle',False)
  assert rows[-1]['client']==[width,width*9//16]
  assert any(r['vtable']=='0x5c6f54' for r in s.controls())
  assert [s.i(0x6a49f0),s.i(0x6a49f4)]==[2560,1440]
c.write_json(out/'acceptance.json',dict(result='passed',switch_both_directions=True,restart_both_sizes=True,save14_both_sizes=True,internal_primary=[2560,1440],engine_sha256=identity['engine_sha256'],wrapper_sha256=c.sha(rt/'ddraw.dll')))
