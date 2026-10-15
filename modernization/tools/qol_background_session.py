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

from install_qol_trial import ROOT, sha, verify_build, no_game_running
from verify_full60_runtime import ProcessEntry, processes
import display

STATE = ROOT / 'modernization/logs/qol-background-session.json'
WRAPPER = ROOT / 'modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll'
WRAPPER_SHA = '1a85a6e0c18b91870db2159d5df87331e21b2a423037b72a94c15035e40bfc58'

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
    p.add_argument('action',choices=['start','move','click','key','capture','status','stop'])
    p.add_argument('values',nargs='*')
    a=p.parse_args()
    if a.action=='start':
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
               'screenshotdir':'.\\modernization\\logs\\qol-snapshots\\'})
        (ROOT/'ddraw.ini').write_text(ini,encoding='cp1252')
        env=dict(os.environ,MM_PROBE_BACKGROUND_INPUT='1',MM_PROBE_LIGHT='1',MM_QOL_TRACE='1')
        launch=subprocess.Popen([str(ROOT/'Chaos-QoL-Trial.exe')],cwd=ROOT,env=env)
        s['launcher_pid']=launch.pid;STATE.write_text(json.dumps(s,indent=2))
        k=kernel_api()
        for _ in range(60):
            ids=[pid for pid,parent,name in processes(k) if parent==launch.pid and name=='chaos-singleplayer-600.exe']
            if ids:s['pid']=ids[0];break
            time.sleep(.2)
        STATE.write_text(json.dumps(s,indent=2))
        if not s['pid']:raise RuntimeError('No engine child; use stop to restore')
        time.sleep(4);send(s,0)
        print(json.dumps(s));return
    s=json.loads(STATE.read_text())
    if a.action=='stop':
        # PIDs must still be owned by the recorded launcher; never kill a reused PID.
        rows=processes(kernel_api())
        owned=[pid for pid,parent,name in rows if pid==s['pid'] and parent==s['launcher_pid'] and name=='chaos-singleplayer-600.exe']
        if owned:subprocess.run(['taskkill','/PID',str(owned[0]),'/F'],capture_output=True)
        time.sleep(.5)
        for r in s['records']:
            b=Path(r['backup'])
            if sha(b)!=r['sha256']:raise RuntimeError('Recovery backup changed')
            Path(r['path']).write_bytes(b.read_bytes())
        changed=[f for f,d in s['saves'].items() if sha(Path(f))!=d]
        s['restored']=True;s['changed_saves']=changed;STATE.write_text(json.dumps(s,indent=2))
        print(json.dumps({'restored':True,'changed_saves':changed}));return
    if s.get('restored'):raise RuntimeError('Session already closed')
    if a.action in ('move','click'):
        x,y=map(int,a.values);send(s,0x200,(y<<16)|x)
        if a.action=='click':
            send(s,0x201,(y<<16)|x);time.sleep(.08);send(s,0x202,(y<<16)|x)
        time.sleep(.3)
    elif a.action=='key':
        u,h=window(s['pid']);u.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
        key=int(a.values[0],0)
        u.PostMessageW(h,0x100,key,1);time.sleep(.08);u.PostMessageW(h,0x101,key,0xc0000001);time.sleep(.3)
    elif a.action=='capture':send(s,0x8000+77)
    from qol_telemetry import snapshot
    print(json.dumps(snapshot(s['pid'])))

if __name__=='__main__':main()
