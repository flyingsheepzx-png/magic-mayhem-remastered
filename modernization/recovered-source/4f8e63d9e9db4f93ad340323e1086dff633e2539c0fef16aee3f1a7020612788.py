"""Recoverable, process-owned Python background input session for QoL research."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from pathlib import Path
import hashlib
ROOT = Path(__file__).resolve().parents[2] / "game"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def no_game_running():
    if any(n in ("chaos.exe", "chaos-hd60-engine.exe", "chaos-singleplayer-600.exe") for _,_,n in processes(kernel_api())):
        raise RuntimeError("Close existing game processes first")
def verify_build():
    expected={"Chaos-HD60-QoL-Trial.exe":"1ed8d1866d74331c015fad7b9190c6c1a6f6553331384db78090d746da272497", "Chaos-HD60-engine.exe":"be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7"}
    for name,digest in expected.items():
        if sha(ROOT/name)!=digest: raise RuntimeError("Unknown " + name)
from verify_hd60_runtime import ProcessEntry, processes
import display

STATE = ROOT / 'modernization/logs/hd-qol-background-session.json'
WRAPPER = ROOT / 'modernization/assets/hd/background-noactivate-ddraw.dll'
WRAPPER_SHA = '217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8'

def kernel_api():
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD]
    k.CreateToolhelp32Snapshot.restype=ctypes.c_void_p
    k.Process32FirstW.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessEntry)]
    k.Process32NextW.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessEntry)]
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    return k

def window(pid):
    u=ctypes.WinDLL('user32',use_last_error=True)
    u.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    found=[]
    cb=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def visit(h,_):
        p=wintypes.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(p))
        if p.value==pid and u.IsWindowVisible(h):found.append(h)
        return True
    u.EnumWindows(cb(visit),0)
    if len(found)!=1:raise RuntimeError(f'Expected one owned window, found {len(found)}')
    return u,found[0]

def send(s, message, coordinates=0):
    u,h=window(s['pid'])
    u.RegisterWindowMessageW.argtypes=[wintypes.LPCWSTR]
    u.SendMessageTimeoutW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM,wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]
    m=u.RegisterWindowMessageW('MagicMayhem.Probe.BackgroundMouse.v1')
    ack=ctypes.c_size_t()
    if not u.SendMessageTimeoutW(h,m,message,coordinates,2,2000,ctypes.byref(ack)) or ack.value!=0x4d4d4247:
        raise RuntimeError('Private mouse channel did not acknowledge input')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['start','move','click','right-click','key','capture','load-test6','load-test2','load-test7','status','stop'])
    p.add_argument('values',nargs='*')
    a=p.parse_args()
    if a.action=='start':
        if STATE.exists():
            prior=json.loads(STATE.read_text())
            if not prior.get('restored'):
                raise RuntimeError('Prior session was not restored; run stop/recover first')
        no_game_running();verify_build()
        if sha(WRAPPER)!=WRAPPER_SHA:raise RuntimeError('Unknown diagnostic wrapper')
        backup=ROOT/'modernization/backups/qol_background'/str(time.time_ns())
        backup.mkdir(parents=True)
        records=[]
        for name in ('ddraw.dll','ddraw.ini'):
            f=ROOT/name;b=backup/name;b.write_bytes(f.read_bytes())
            records.append({'path':str(f),'backup':str(b),'sha256':sha(f)})
        s={'records':records,'pid':None,'launcher_pid':None,
           'saves':{str(f):sha(f) for f in (ROOT/'Save').glob('*.sav')}}
        STATE.write_text(json.dumps(s,indent=2))
        (ROOT/'ddraw.dll').write_bytes(WRAPPER.read_bytes())
        ini=display.update_ddraw((backup/'ddraw.ini').read_text(encoding='cp1252'),
              {'windowed':'true','noactivateapp':'true','nonexclusive':'true',
               'screenshotdir':'.\\modernization\\logs\\hd-qol-snapshots\\'})
        (ROOT/'ddraw.ini').write_text(ini,encoding='cp1252')
        env=dict(os.environ,MM_PROBE_BACKGROUND_INPUT='1',MM_PROBE_LIGHT='1',MM_QOL_TRACE='1')
        launch=subprocess.Popen([str(ROOT/'Chaos-HD60-QoL-Trial.exe')],cwd=ROOT,env=env)
        s['launcher_pid']=launch.pid;STATE.write_text(json.dumps(s,indent=2))
        k=kernel_api()
        for _ in range(60):
            ids=[pid for pid,parent,name in processes(k) if parent==launch.pid and name=='chaos-hd60-engine.exe']
            if ids:s['pid']=ids[0];break
            time.sleep(.2)
        STATE.write_text(json.dumps(s,indent=2))
        if not s['pid']:raise RuntimeError('No engine child; use stop to restore')
        time.sleep(4);send(s,0)
        print(json.dumps(s));return
    s=json.loads(STATE.read_text())
    if a.action=='stop':
        if s.get('restored'):
            print(json.dumps({'restored':True,'already_closed':True,'changed_saves':s.get('changed_saves',[])}));return
        # PIDs must still be owned by the recorded launcher; never kill a reused PID.
        rows=processes(kernel_api())
        owned=[pid for pid,parent,name in rows if pid==s['pid'] and parent==s['launcher_pid'] and name=='chaos-hd60-engine.exe']
        if owned:subprocess.run(['taskkill','/PID',str(owned[0]),'/F'],capture_output=True)
        time.sleep(.5)
        for r in s['records']:
            b=Path(r['backup'])
            if sha(b)!=r['sha256']:raise RuntimeError('Recovery backup changed')
            Path(r['path']).write_bytes(b.read_bytes())
        changed=[f for f,d in s['saves'].items() if not Path(f).exists() or sha(Path(f))!=d]
        for name in ('ddraw.dll','ddraw.ini'):
            original=next(r for r in s['records'] if Path(r['path']).name==name)
            if sha(Path(original['path']))!=original['sha256']:
                raise RuntimeError('Wrapper/config restoration failed: '+name)
        s['restored']=True;s['changed_saves']=changed;STATE.write_text(json.dumps(s,indent=2))
        print(json.dumps({'restored':True,'changed_saves':changed}));return
    if s.get('restored'):raise RuntimeError('Session already closed')
    if not any(pid==s['pid'] and parent==s['launcher_pid'] and name=='chaos-hd60-engine.exe' for pid,parent,name in processes(kernel_api())):
        raise RuntimeError('Recorded engine PID is no longer owned')
    from qol_telemetry import snapshot
    snapshot(s['pid'])  # Verify the exact child image before dispatching input.
    if a.action in ('move','click','right-click'):
        x,y=map(int,a.values)
        if not (0<=x<1120 and 0<=y<840):raise RuntimeError('Outside native surface')
        send(s,0x200,(y<<16)|x)
        if a.action=='click':
            send(s,0x201,(y<<16)|x);time.sleep(.08);send(s,0x202,(y<<16)|x)
        elif a.action=='right-click':
            send(s,0x204,(y<<16)|x);time.sleep(.08);send(s,0x205,(y<<16)|x)
        time.sleep(.3)
    elif a.action=='key':
        u,h=window(s['pid']);u.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
        key=int(a.values[0],0)
        u.PostMessageW(h,0x100,key,1);time.sleep(.08);u.PostMessageW(h,0x101,key,0xc0000001);time.sleep(.3)
    elif a.action=='capture':send(s,0x8000+77)
    elif a.action in ('load-test6','load-test2','load-test7'):
        fixture=ROOT/('Save/'+a.action.removeprefix('load-')+'.sav')
        expected='4031940a5838ae30ca94c24e103521c2ccf9d8e45cf7f12b0d1d1cea2144209b' if a.action=='load-test6' else '56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d'
        if a.action=='load-test7': expected=json.loads((ROOT/'modernization/config/qol-fixtures.json').read_text())['test7.sav']
        if sha(fixture)!=expected: raise RuntimeError('Unknown save fixture')
        def click(x,y):
            c=(y<<16)|x
            for m in (0x200,0x201,0x202):
                send(s,m,c);time.sleep(.08 if m==0x201 else .03)
        click(560,532);time.sleep(1.5)
        saves=sorted((ROOT/'Save').glob('*.sav'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
        row=[i for i,p in enumerate(saves) if p.name.lower()==fixture.name.lower()]
        if len(row)!=1 or row[0]>10:raise RuntimeError('fixture row missing or ambiguous')
        click(560,337+row[0]*25);time.sleep(.3);click(196,777);time.sleep(4)
        send(s,0x8000+77)
    from qol_telemetry import snapshot
    print(json.dumps(snapshot(s['pid'])))

if __name__=='__main__':main()
