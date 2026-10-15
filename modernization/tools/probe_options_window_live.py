"""Owned menu switches and restart tests for item2; player runtime untouched."""
import ctypes,time,shutil,re,json
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
import prepare_options_window as prep
from install_11_minimap_v2 import resources
ctypes.windll.user32.SetProcessDPIAware();p=prep.base.DEST
identity=dict(version='1.1',package=str(p),launcher_name=prep.base.ENTRY,launcher_sha256=c.sha(p/prep.base.ENTRY),engine_sha256=c.ENGINES['1.1'])
out=prep.b.ROOT/'modernization/logs/remastered-ui/options-window-acceptance-v1';out.mkdir(exist_ok=False)
rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav')
candidate=prep.OUT/'candidate.exe';assert all(resources(candidate)[i]==resources(p/prep.base.ENTRY)[i] for i in [101,103])
shutil.copy2(candidate,rt.parent/prep.base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
shutil.copy2(prep.OUT/'wrapper/bin/Release/ddraw.dll',rt/'ddraw.dll')
text=rt/'CFG/interface screens text.cfg';text.write_bytes(prep.label_bytes(text.read_bytes()))
prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
rows=[]
def measure(s,name,width,borderless):
 rect=W.RECT();hw=s.window();s.u.GetClientRect(hw,ctypes.byref(rect))
 s.u.GetWindowLongW.argtypes=[W.HWND,ctypes.c_int];s.u.GetWindowLongW.restype=W.LONG
 style=s.u.GetWindowLongW(hw,-16);row=dict(name=name,client=[rect.right,rect.bottom],style=hex(style&0xffffffff),ini=(rt/'remastered-settings.ini').read_text(),animation_native=s.i(0x6de6f1));rows.append(row);c.write_json(out/'measurements.json',rows);print(row,flush=True)
 assert row['client']==[width,width*9//16]
 assert bool(style&0xc00000)==(not borderless)
 assert [s.i(0x6a49f0),s.i(0x6a49f4)]==[2560,1440]
with c.session_class()(identity,rt,out/'switch',110) as s:
 initial=s.i(0x6de6f1)
 for width,borderless in [(1920,False),(1920,True),(2560,True),(2560,False)]:
  s.click_base(640,576);time.sleep(.35)
  s.click_base(290,339 if width==2560 else 369);s.click_base(770,369 if borderless else 339)
  s.shot(str(width)+'-'+str(borderless),False);s.click_base(352,660);time.sleep(.5)
  measure(s,'menu-switch',width,borderless);assert s.i(0x6de6f1)==initial
 s.load_fixture('14');time.sleep(.4);measure(s,'save14',2560,False);s.shot('battle',False)
for mode in ['borderless','windowed']:
 (rt/'remastered-settings.ini').write_text('[display]\nresolution=1920x1080\nwindow_mode='+mode+'\n')
 with c.session_class()(identity,rt,out/('restart-'+mode),90) as s:
  measure(s,'restart-'+mode,1920,mode=='borderless')
  s.click_base(640,576);time.sleep(.4);s.shot('restored-mode',False)
  s.click_base(938,660);time.sleep(.3);s.load_fixture('14');time.sleep(.4);measure(s,'battle-'+mode,1920,mode=='borderless');s.shot('battle',False)
acceptance=dict(result='passed',wrapper_sha256=c.sha(rt/'ddraw.dll'),candidate_sha256=c.sha(candidate),live_switch_four_combinations=True,restart_both_modes=True,save14_both_modes=True,native_animation_unchanged=True,evidence=str(out))
c.write_json(prep.OUT/'runtime-acceptance.json',acceptance)
