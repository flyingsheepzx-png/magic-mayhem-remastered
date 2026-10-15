"""Actual battle logic-boundary counts after native options confirmation."""
import ctypes,time,shutil,re,json,pefile
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
import prepare_options_speed as prep
from install_11_minimap_v2 import resources
ctypes.windll.user32.SetProcessDPIAware();p=prep.base.DEST
identity=dict(version='1.1',package=str(p),launcher_name=prep.base.ENTRY,launcher_sha256=c.sha(p/prep.base.ENTRY),engine_sha256=c.ENGINES['1.1'])
out=prep.b.ROOT/'modernization/logs/remastered-ui/options-speed-acceptance-v2';out.mkdir(exist_ok=False)
rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav')
candidate=prep.OUT/'candidate.exe';assert all(resources(candidate)[i]==resources(p/prep.base.ENTRY)[i] for i in [101,103])
shutil.copy2(candidate,rt.parent/prep.base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
text=rt/'CFG/interface screens text.cfg';text.write_bytes(prep.label_bytes(text.read_bytes()))
screen=rt/prep.SCREEN;screen.write_bytes(prep.screen_bytes(screen.read_bytes()))
prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
pe=pefile.PE(str(prep.OUT/'qol_bindings.dll'));counter=next(e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name==b'mm_options_logic_updates')
rows=[]
for fps,y in [(40,195),(30,225),(20,255)]:
 s=c.session_class()(identity,rt,out/('run-'+str(fps)),90);s.diagnostic_environment={'MM_PROBE_OPTIONS_LOGIC':'1'}
 with s:
  hook=__import__('verify_hd60_runtime').read(s.k,s.handle,0x4a990c,5);target=0x4a9911+int.from_bytes(hook[1:],'little',signed=True)
  s.k.VirtualQueryEx.argtypes=[W.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t];s.k.VirtualQueryEx.restype=ctypes.c_size_t
  # Portable MEMORY_BASIC_INFORMATION64 layout for the 64-bit controller.
  class MBI(ctypes.Structure):
   _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),('AllocationProtect',W.DWORD),('PartitionId',W.WORD),('RegionSize',ctypes.c_size_t),('State',W.DWORD),('Protect',W.DWORD),('Type',W.DWORD)]
  mbi=MBI();assert s.k.VirtualQueryEx(s.handle,target,ctypes.byref(mbi),ctypes.sizeof(mbi));address=mbi.AllocationBase+counter
  s.click_base(640,576);time.sleep(.35);s.click_base(770,y);s.shot('selected-'+str(fps),False);s.click_base(352,660);time.sleep(.4)
  assert s.i(0x6de6fd)==fps and s.i(0x6dbe99)==fps
  assert s.i(0x6de6f9)==1000//fps and s.i(0x6dbe95)==1000//fps
  assert re.search(rb'MaxFramesPerSec='+str(fps).encode()+rb'\b',prefs.read_bytes())
  s.load_fixture('14');time.sleep(1)
  t=time.perf_counter();a=s.i(address);time.sleep(6);elapsed=time.perf_counter()-t;updates=s.i(address)-a;rate=updates/elapsed
  row=dict(fps=fps,elapsed=elapsed,logic_updates=updates,measured_logic_rate=rate,scheduler_ms=s.i(0x6dbe95),clock_start=s.i(0x6c4830));rows.append(row);c.write_json(out/'measurements.json',rows);print(row,flush=True)
  assert fps*.88<=rate<=fps*1.08
  s.shot('battle-'+str(fps),False)
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
