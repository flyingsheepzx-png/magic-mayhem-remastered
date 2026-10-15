"""Measure real successful Direct3D9 Present calls and independent battle logic."""
import ctypes,time,shutil,re,json,pefile
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
import prepare_options_render as prep
from install_11_minimap_v2 import resources
ctypes.windll.user32.SetProcessDPIAware();p=prep.base.DEST
identity=dict(version='1.1',package=str(p),launcher_name=prep.base.ENTRY,launcher_sha256=c.sha(p/prep.base.ENTRY),engine_sha256=c.ENGINES['1.1'])
out=prep.b.ROOT/'modernization/logs/remastered-ui/options-font-observation-v1';out.mkdir(exist_ok=False)
rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav');candidate=prep.OUT/'candidate.exe'
assert all(resources(candidate)[i]==resources(p/prep.base.ENTRY)[i] for i in [101,103])
shutil.copy2(candidate,rt.parent/prep.base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
shutil.copy2(prep.OUT/'wrapper/bin/Release/ddraw.dll',rt/'ddraw.dll')
text=rt/'CFG/interface screens text.cfg';# already installed
screen=rt/prep.SCREEN;# already installed
prefs=rt/'CFG/prefs.cfg';prefs.write_bytes(re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',prefs.read_bytes()))
pe=pefile.PE(str(prep.OUT/'qol_bindings.dll'));counter=next(e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name==b'mm_options_logic_updates')
rows=[]
def query(s,event):
 ack=ctypes.c_size_t();assert s.u.SendMessageTimeoutW(s.window(),s.channel,event,0,2,2000,ctypes.byref(ack));return ack.value
class MBI(ctypes.Structure):
 _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),('AllocationProtect',W.DWORD),('PartitionId',W.WORD),('RegionSize',ctypes.c_size_t),('State',W.DWORD),('Protect',W.DWORD),('Type',W.DWORD)]

class MODULEENTRY32W(ctypes.Structure):
 _fields_=[('dwSize',W.DWORD),('th32ModuleID',W.DWORD),('th32ProcessID',W.DWORD),('GlblcntUsage',W.DWORD),('ProccntUsage',W.DWORD),('modBaseAddr',ctypes.c_void_p),('modBaseSize',W.DWORD),('hModule',W.HMODULE),('szModule',W.WCHAR*256),('szExePath',W.WCHAR*260)]
s=c.session_class()(identity,rt,out/'run',80)
with s:
 s.click_base(640,576);time.sleep(.4);s.shot('font',False)
 s.k.Module32FirstW.argtypes=[W.HANDLE,ctypes.POINTER(MODULEENTRY32W)];s.k.Module32NextW.argtypes=s.k.Module32FirstW.argtypes
 snap=s.k.CreateToolhelp32Snapshot(0x18,s.pid);m=MODULEENTRY32W();m.dwSize=ctypes.sizeof(m);ok=s.k.Module32FirstW(snap,ctypes.byref(m));base=None
 while ok:
  if m.szModule.lower()=='chaos95.dll':base=m.modBaseAddr
  ok=s.k.Module32NextW(snap,ctypes.byref(m))
 s.k.CloseHandle(snap);assert base
 from verify_hd60_runtime import read
 import struct
 cache=[]
 for n in range(50):
  slot=base+0x55664+n*0x9ca;code=struct.unpack('<H',read(s.k,s.handle,slot+4,2))[0]
  if not code:continue
  header=struct.unpack('<10I',read(s.k,s.handle,slot+6,40));size=header[0]
  cache.append(dict(code=hex(code),header=header))
  if code in [0xd6a1,0xc2ca,0xc2df,0xbcaD,0xbfec,0xc8be]:
   data=read(s.k,s.handle,slot+6,size);(out/(hex(code)+'.bin')).write_bytes(data)
 c.write_json(out/'cache.json',dict(base=base,cache=cache));print(cache,flush=True)
