"""Measure real successful Direct3D9 Present calls and independent battle logic."""
import ctypes,time,shutil,re,json,pefile
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
import prepare_options_render as prep
from install_11_minimap_v2 import resources
ctypes.windll.user32.SetProcessDPIAware();p=prep.base.DEST
identity=dict(version='1.1',package=str(p),launcher_name=prep.base.ENTRY,launcher_sha256=c.sha(p/prep.base.ENTRY),engine_sha256=c.ENGINES['1.1'])
out=prep.b.ROOT/'modernization/logs/remastered-ui/options-render-acceptance-v1';out.mkdir(exist_ok=False)
rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav');candidate=prep.OUT/'candidate.exe'
assert all(resources(candidate)[i]==resources(p/prep.base.ENTRY)[i] for i in [101,103])
shutil.copy2(candidate,rt.parent/prep.base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
shutil.copy2(prep.OUT/'wrapper/bin/Release/ddraw.dll',rt/'ddraw.dll')
text=rt/'CFG/interface screens text.cfg';text.write_bytes(prep.label_bytes(text.read_bytes()))
screen=rt/prep.SCREEN;screen.write_bytes(prep.screen_bytes(screen.read_bytes()))
prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
pe=pefile.PE(str(prep.OUT/'qol_bindings.dll'));counter=next(e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name==b'mm_options_logic_updates')
rows=[]
def query(s,event):
 ack=ctypes.c_size_t();assert s.u.SendMessageTimeoutW(s.window(),s.channel,event,0,2,2000,ctypes.byref(ack));return ack.value
class MBI(ctypes.Structure):
 _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),('AllocationProtect',W.DWORD),('PartitionId',W.WORD),('RegionSize',ctypes.c_size_t),('State',W.DWORD),('Protect',W.DWORD),('Type',W.DWORD)]
for fps,y in [(60,483),(120,513)]:
 s=c.session_class()(identity,rt,out/('run-'+str(fps)),100);s.diagnostic_environment={'MM_PROBE_OPTIONS_LOGIC':'1'}
 with s:
  native=s.i(0x6de6f5)
  s.click_base(640,576);time.sleep(.35);s.click_base(770,y);s.shot('selected-render',False);s.click_base(352,660);time.sleep(.6)
  assert query(s,0x8053)==fps and s.i(0x6de6f5)==native
  s.load_fixture('14');time.sleep(1)
  hook=__import__('verify_hd60_runtime').read(s.k,s.handle,0x4a990c,5);target=0x4a9911+int.from_bytes(hook[1:],'little',signed=True)
  s.k.VirtualQueryEx.argtypes=[W.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t];s.k.VirtualQueryEx.restype=ctypes.c_size_t
  mbi=MBI();assert s.k.VirtualQueryEx(s.handle,target,ctypes.byref(mbi),ctypes.sizeof(mbi));address=mbi.AllocationBase+counter
  t=time.perf_counter();a=query(s,0x8052);logic=s.i(address);time.sleep(6);elapsed=time.perf_counter()-t;present=query(s,0x8052)-a;updates=s.i(address)-logic
  row=dict(fps=fps,elapsed=elapsed,successful_presents=present,present_rate=present/elapsed,logic_updates=updates,logic_rate=updates/elapsed);rows.append(row);print(row,flush=True);c.write_json(out/'measurements.json',rows)
  assert fps*.88<=row['present_rate']<=fps*1.10
  assert 27<=row['logic_rate']<=33 and s.i(0x6de6fd)==30
  s.shot('battle',False)
for fps in [60,120]:
 (rt/'remastered-settings.ini').write_text('[display]\nresolution=1920x1080\nwindow_mode=borderless\nrender_fps='+str(fps)+'\n')
 with c.session_class()(identity,rt,out/('restart-'+str(fps)),65) as s:
  assert query(s,0x8053)==fps;s.click_base(640,576);time.sleep(.4);s.shot('restored-render',False)
  from PIL import Image
  image=Image.open(s.run/'restored-render-2560x1440.png');dots=[image.getpixel((1538,y)) for y in [966,1026]]
  assert max(dots[[60,120].index(fps)])>90 and max(dots[1-[60,120].index(fps)])<30
  print('restored render',fps,dots,flush=True)
c.write_json(prep.OUT/'runtime-acceptance.json',dict(result='passed',candidate_sha256=c.sha(candidate),wrapper_sha256=c.sha(rt/'ddraw.dll'),render_measurements=rows,restart_both_rates=True,native_dialogue_unchanged=True,evidence=str(out),scope='successful Direct3D9 presentations; repeated source frames allowed; not unique simulation frames'))
