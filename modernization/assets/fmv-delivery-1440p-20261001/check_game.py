"""Bounded owned-process playback check; touches only this isolated playtest."""
import argparse,ctypes,json,os,shutil,subprocess,sys,time
from ctypes import wintypes as W
from pathlib import Path
from PIL import Image
import numpy as np
from deliver import ROOT,sha
sys.path.insert(0,str(ROOT.parents[2]/'modernization/tools'))
import wide169_trial as w
def snapshot(hwnd,path):
 u=ctypes.WinDLL('user32');g=ctypes.WinDLL('gdi32')
 u.GetDC.argtypes=[W.HWND];u.GetDC.restype=W.HDC;u.GetClientRect.argtypes=[W.HWND,ctypes.POINTER(W.RECT)]
 u.PrintWindow.argtypes=[W.HWND,W.HDC,W.UINT];u.ReleaseDC.argtypes=[W.HWND,W.HDC]
 g.CreateCompatibleDC.argtypes=[W.HDC];g.CreateCompatibleDC.restype=W.HDC;g.CreateCompatibleBitmap.argtypes=[W.HDC,ctypes.c_int,ctypes.c_int];g.CreateCompatibleBitmap.restype=W.HBITMAP
 g.SelectObject.argtypes=[W.HDC,W.HANDLE];g.SelectObject.restype=W.HANDLE;g.DeleteObject.argtypes=[W.HANDLE];g.DeleteDC.argtypes=[W.HDC]
 class BI(ctypes.Structure):_fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bitcount',W.WORD),('compression',W.DWORD),('sizeimage',W.DWORD),('x',W.LONG),('y',W.LONG),('used',W.DWORD),('important',W.DWORD)]
 g.GetDIBits.argtypes=[W.HDC,W.HBITMAP,W.UINT,W.UINT,ctypes.c_void_p,ctypes.c_void_p,W.UINT]
 r=W.RECT();u.GetClientRect(hwnd,ctypes.byref(r));ww,hh=r.right,r.bottom
 dc=u.GetDC(hwnd);mem=g.CreateCompatibleDC(dc);bmp=g.CreateCompatibleBitmap(dc,ww,hh);old=g.SelectObject(mem,bmp)
 try:
  ok=u.PrintWindow(hwnd,mem,2);bi=BI(40,ww,-hh,1,32,0,ww*hh*4,0,0,0,0);buf=ctypes.create_string_buffer(ww*hh*4)
  got=g.GetDIBits(mem,bmp,0,hh,buf,ctypes.byref(bi),0);assert got==hh
  im=Image.frombuffer('RGB',(ww,hh),buf.raw,'raw','BGRX',0,1);im.save(path)
  arr=np.asarray(im);return {'size':[ww,hh],'PrintWindow':ok,'sha256':sha(path),'std_rgb':float(arr.std()),'bright_fraction':float((arr.max(2)>40).mean())}
 finally:g.SelectObject(mem,old);g.DeleteObject(bmp);g.DeleteDC(mem);u.ReleaseDC(hwnd,dc)
def main():
 a=argparse.ArgumentParser();a.add_argument('--label',required=True);a.add_argument('--first',default='Medieval');a.add_argument('--second',default='Intro1');a.add_argument('--seconds',type=int,default=112);a.add_argument('--skip-at',type=int);o=a.parse_args()
 k=w.configured_kernel();assert not any(n.startswith(('chaos','magicmayhem')) for _,_,n in w.processes(k)),'another game active'
 lab=ROOT/'playtest';rt=lab/'runtime';build=json.loads((ROOT/'player-build.json').read_text(encoding='utf-8'));assert sha(rt/'Chaos-Wide169-engine.exe')==build['engine_sha256'];assert sha(lab/'FMV-1440p-Playtest.exe')==build['launcher_sha256']
 out=ROOT/'playback-checks'/o.label;out.mkdir(parents=True,exist_ok=False)
 for source,target in [(ROOT/(o.first+'.mp4'),rt/'FMV/intro0.mp4'),(ROOT/(o.second+'.mp4'),rt/'FMV/Intro1.mp4')]:shutil.copy2(source,target);assert sha(source)==sha(target)
 events=rt/'fmv-h264-events.jsonl'
 if events.exists():shutil.copy2(events,out/'prior-events.jsonl');events.write_bytes(b'')
 env=dict(os.environ,MM_FMV_H264='1',MM_PROBE_BACKGROUND_INPUT='1')
 p=subprocess.Popen([str(lab/'FMV-1440p-Playtest.exe')],cwd=lab,env=env);child=None;h=None;records=[];started=time.monotonic();audio=None;audio_file=None
 u=ctypes.WinDLL('user32');u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
 try:
  while time.monotonic()-started<o.seconds:
   elapsed=time.monotonic()-started
   if child is None:
    ids=[pid for pid,pp,n in w.processes(k) if pp==p.pid and n=='chaos-wide169-engine.exe']
    if ids:assert len(ids)==1;child=ids[0];h=k.OpenProcess(0x101001,False,child)
   hwnd=None
   if child:
    matches=[]
    CB=ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)];u.IsWindowVisible.argtypes=[W.HWND]
    @CB
    def visit(win,param):
     pid=W.DWORD();u.GetWindowThreadProcessId(win,ctypes.byref(pid))
     if pid.value==child and u.IsWindowVisible(win):matches.append(win)
     return True
    u.EnumWindows(visit,0)
    if matches:hwnd=matches[0]
   if hwnd and (not records or elapsed-records[-1]['time']>=8):
    row=snapshot(hwnd,out/f'{int(elapsed):03d}s.png');row['time']=elapsed;records.append(row);print('CAPTURE',o.label,round(elapsed),row['size'],round(row['std_rgb'],2),flush=True)
   if child and audio is None and elapsed>5:
    audio_file=(out/'audio-session.json').open('w');audio=subprocess.Popen([str(ROOT/'audio_meter.exe'),str(child)],stdout=audio_file,stderr=audio_file)
   if hwnd and o.skip_at is not None and elapsed>=o.skip_at:
    u.PostMessageW(hwnd,0x100,0x1b,0);u.PostMessageW(hwnd,0x101,0x1b,0);o.skip_at=None;print('SKIP_SENT',flush=True)
   if p.poll() is not None:print('LAUNCHER_EXIT',p.returncode,flush=True);break
   time.sleep(1)
 finally:
  if audio:
   try:audio.wait(timeout=10)
   except subprocess.TimeoutExpired:audio.terminate();audio.wait(timeout=5)
  if audio_file:audio_file.close()
  if h:k.TerminateProcess(h,0);k.WaitForSingleObject(h,5000);k.CloseHandle(h)
  if p.poll() is None:p.terminate();p.wait(timeout=5)
  if events.exists():shutil.copy2(events,out/'events.jsonl')
  (out/'report.json').write_text(json.dumps({'first':o.first,'second':o.second,'source_engine_sha256':build['engine_sha256'],'launcher_sha256':build['launcher_sha256'],'captures':records,'installed_runtime_modified':False},indent=2))
 print('CHECK_SAVED',out,flush=True)
if __name__=='__main__':main()
