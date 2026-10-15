"""Owned close reproduction with Windows read-only wait-chain diagnostics."""
import argparse,ctypes,time,json,re
from ctypes import wintypes as W
import compare_remastered_ui_11 as c
class ThreadWait(ctypes.Structure):
 _fields_=[('ProcessId',W.DWORD),('ThreadId',W.DWORD),('WaitTime',W.DWORD),('ContextSwitches',W.DWORD)]
class LockWait(ctypes.Structure):
 _fields_=[('ObjectName',W.WCHAR*128),('Timeout',ctypes.c_longlong),('Alertable',W.BOOL)]
class Info(ctypes.Union):_fields_=[('ThreadObject',ThreadWait),('LockObject',LockWait)]
class Node(ctypes.Structure):_fields_=[('ObjectType',ctypes.c_int),('ObjectStatus',ctypes.c_int),('info',Info)]
def chains(pid):
 # Toolhelp avoids slow shell startup and the process-exit/null-TID race.
 class Entry(ctypes.Structure):
  _fields_=[('size',W.DWORD),('usage',W.DWORD),('tid',W.DWORD),('pid',W.DWORD),('base',W.LONG),('delta',W.LONG),('flags',W.DWORD)]
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];k.CreateToolhelp32Snapshot.restype=W.HANDLE
 k.Thread32First.argtypes=k.Thread32Next.argtypes=[W.HANDLE,ctypes.POINTER(Entry)]
 k.CloseHandle.argtypes=[W.HANDLE]
 snap=k.CreateToolhelp32Snapshot(4,0);tids=[]
 if snap==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 try:
  entry=Entry();entry.size=ctypes.sizeof(entry);ok=k.Thread32First(snap,ctypes.byref(entry))
  while ok:
   if entry.pid==pid:tids.append(entry.tid)
   ok=k.Thread32Next(snap,ctypes.byref(entry))
 finally:k.CloseHandle(snap)
 a=ctypes.WinDLL('advapi32',use_last_error=True);a.OpenThreadWaitChainSession.argtypes=[W.DWORD,ctypes.c_void_p];a.OpenThreadWaitChainSession.restype=W.HANDLE
 a.GetThreadWaitChain.argtypes=[W.HANDLE,ctypes.c_size_t,W.DWORD,W.DWORD,ctypes.POINTER(W.DWORD),ctypes.POINTER(Node),ctypes.POINTER(W.BOOL)];a.GetThreadWaitChain.restype=W.BOOL
 a.CloseThreadWaitChainSession.argtypes=[W.HANDLE]
 session=a.OpenThreadWaitChainSession(0,None);rows=[]
 try:
  for tid in tids:
   count=W.DWORD(16);nodes=(Node*16)();cycle=W.BOOL()
   ok=a.GetThreadWaitChain(session,0,0,tid,ctypes.byref(count),nodes,ctypes.byref(cycle))
   row=dict(tid=tid,ok=bool(ok),error=ctypes.get_last_error() if not ok else 0,cycle=bool(cycle.value),nodes=[])
   if ok:
    for n in nodes[:min(count.value,16)]:
     v=dict(type=n.ObjectType,status=n.ObjectStatus)
     if n.ObjectType==8:v.update(pid=n.info.ThreadObject.ProcessId,tid=n.info.ThreadObject.ThreadId,wait=n.info.ThreadObject.WaitTime)
     else:v.update(name=n.info.LockObject.ObjectName)
     row['nodes'].append(v)
   rows.append(row)
 finally:a.CloseThreadWaitChainSession(session)
 return rows
def run(name,mode,game_close=False):
 ctypes.windll.user32.SetProcessDPIAware();p=c.CANDIDATE;identity=c.verify_package(p,'1.1',c.sha(p/'manifest.json'))
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 Base=c.session_class()
 class Trial(Base):
  def start(self):
   ini=self.lab/'ddraw.ini';raw=ini.read_bytes();st=ini.stat()
   try:
    if game_close:
     changed,n=re.subn(rb'(?m)^game_handles_close=false\r?$',b'game_handles_close=true',raw,count=1)
     assert n==1
     ini.write_bytes(changed)
    return super().start()
   finally:
    # Super captures mutable backup before launching. Restore that backup's
    # original bytes too, so __exit__ retains the diagnostic-only override.
    if game_close and ini in self.mutable:
     backup,_,at,mt=self.mutable[ini];backup.write_bytes(raw)
     self.mutable[ini]=(backup,c.sha(backup),st.st_atime_ns,st.st_mtime_ns)
     c.write_json(self.run/'backup.json',{str(p.relative_to(self.lab)):{'sha256':row[1],'atime_ns':row[2],'mtime_ns':row[3]} for p,row in self.mutable.items()})
    elif game_close:ini.write_bytes(raw)
 s=Trial(identity,p/'runtime',out/'1.1',60)
 with s:
  c.write_json(out/'before-waits.json',chains(s.pid));hwnd=s.window()
  s.u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];s.u.PostMessageW.restype=W.BOOL
  msg,wp,lp={'system':(0x112,0xf060,0),'close':(0x10,0,0),'altf4':(0x104,0x73,0x203e0001)}[mode]
  assert s.u.PostMessageW(hwnd,msg,wp,lp)
  started=time.perf_counter()
  exited=s.k.WaitForSingleObject(s.stop_handle,1500)==0
  if not exited:c.write_json(out/'early-waits.json',chains(s.pid))
  if not exited:exited=s.k.WaitForSingleObject(s.stop_handle,6500)==0
  if exited:
   try:s.proc.wait(timeout=4)
   except Exception:pass
  s.result['close_exited']=exited;s.result['launcher_exited']=s.proc.poll() is not None
  if not exited:c.write_json(out/'after-waits.json',chains(s.pid))
  c.write_json(out/'exit-state.json',dict(exited=exited,launcher_exited=s.proc.poll() is not None,pid=s.pid,hwnd=hwnd,observed_seconds=time.perf_counter()-started))
 print(out,exited)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--mode',choices=['system','close','altf4'],default='system');p.add_argument('--game-close',action='store_true');a=p.parse_args();run(a.name,a.mode,a.game_close)
