"""Compare left and right portrait event paths in a bounded owned session."""
import json,os,sys,time,ctypes,pefile,shutil
from ctypes import wintypes as W
from pathlib import Path
from wide169_trial import Session,ROOT,GAME,sha
from verify_wide169_input_map import state
from verify_hd60_runtime import read
os.environ['MM_ALLOW_NATIVE_CLIENT']='1';os.environ['MM_ALLOW_SCALED_CLIENT']='1'
entry=GAME/'Chaos-Wide169-Trial.exe';original=entry.read_bytes()
expected=json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']['files']['game/Chaos-Wide169-Trial.exe']
if sha(original)!=expected:raise RuntimeError('Baseline identity mismatch')
candidate=GAME/'Chaos-Wide169-Portrait-Diag.exe'
if candidate.exists():raise RuntimeError('Diagnostic launcher already exists')
shutil.copy2(ROOT/'modernization/build/Chaos-Wide169-Trial.exe',candidate)
os.environ['MM_WIDE169_DIAGNOSTIC_LAUNCHER']=str(candidate)
try:
 with Session() as s:
    s.load('test7');s.key(0x5a);s.key(ord('Q'));time.sleep(.2)
    class Module(ctypes.Structure):
        _fields_=[('dwSize',W.DWORD),('th32ModuleID',W.DWORD),('th32ProcessID',W.DWORD),
            ('GlblcntUsage',W.DWORD),('ProccntUsage',W.DWORD),('modBaseAddr',ctypes.c_void_p),
            ('modBaseSize',W.DWORD),('hModule',ctypes.c_void_p),('szModule',W.WCHAR*256),
            ('szExePath',W.WCHAR*260)]
    k=s.k;k.Module32FirstW.argtypes=[ctypes.c_void_p,ctypes.POINTER(Module)]
    k.Module32NextW.argtypes=[ctypes.c_void_p,ctypes.POINTER(Module)]
    snap=k.CreateToolhelp32Snapshot(0x18,s.pid)
    if snap==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    m=Module();m.dwSize=ctypes.sizeof(m);base=None
    try:
        if k.Module32FirstW(snap,ctypes.byref(m)):
            while True:
                if m.szModule.lower().startswith('mm-qol-'):base=m.modBaseAddr;break
                if not k.Module32NextW(snap,ctypes.byref(m)):break
    finally:k.CloseHandle(snap)
    if not base:raise RuntimeError('QoL module not found')
    pe=pefile.PE(str(ROOT/'modernization/runtime/wide169/qol_bindings.dll'))
    offsets={e.name.decode():e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols}
    def counters():return {n:list(int.from_bytes(read(s.k,s.handle,base+r+4*i,4),'little') for i in range(16)) for n,r in offsets.items()}
    print('before',counters(),flush=True)
    s.message(0x200,1215,650);time.sleep(.2)
    for event in ([0x200,0x204,0x205] if '--right' in sys.argv else [0x200,0x201,0x202]):
        print('event',hex(event),flush=True)
        s.message(event,1215,650);time.sleep(.09)
        print('counts',counters(),flush=True)
    time.sleep(.5)
    s.result['post_click']=state(s)
    print(json.dumps(s.result['post_click']))
finally:
 if sha(entry.read_bytes())!=expected:raise RuntimeError('Installed launcher changed')
 candidate.unlink()
