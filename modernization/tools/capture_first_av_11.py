"""Attach bounded x86 exception observer to a user-owned, hash-verified game."""
import argparse,ctypes,json,subprocess,time
from ctypes import wintypes as W
from pathlib import Path
import build_remastered_11 as b
from verify_hd60_runtime import configured_kernel,read

def run(pid,seconds):
    k=configured_kernel();k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
    k.QueryFullProcessImageNameW.restype=W.BOOL
    handle=k.OpenProcess(0x1010,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        path=ctypes.create_unicode_buffer(32768);size=W.DWORD(32768)
        if not k.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
        engine=Path(path.value).resolve()
        from build_11_surface_lifecycle import DEST,ENTRY
        if engine==(DEST/'runtime/Chaos-Wide169-engine.exe').resolve():
            package=DEST;manifest_name='release-manifest.json';launcher=ENTRY
        else:
            assert engine==(b.TARGET/'runtime/Chaos-Wide169-engine.exe').resolve()
            package=b.TARGET;manifest_name='manifest.json';launcher='MagicMayhem-Remastered-1.1.exe'
        manifest=json.loads((package/manifest_name).read_text(encoding='utf-8'))
        assert b.sha(engine)==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
        assert b.sha(package/launcher)==manifest['launcher_sha256']
        assert read(k,handle,0x400000,2)==b'MZ'
    finally:k.CloseHandle(handle)
    out=b.ROOT/'modernization/logs/remastered-ui'/f'first-av-p{pid}-{time.time_ns()}'
    out.mkdir(exist_ok=False)
    helper=b.ROOT/'modernization/build/hang-dump-x86/capture_first_av_x86.exe'
    b.write(out/'identity.json',dict(pid=pid,engine_sha256=b.sha(engine),launcher_sha256=manifest['launcher_sha256'],
        helper_sha256=b.sha(helper),seconds=seconds,scope='debugger event observation, exception dumps; no memory writes or termination'))
    print('CAPTURE_DIRECTORY',out,flush=True)
    subprocess.run([str(helper),str(pid),str(engine),str(out),str(seconds)],check=True,timeout=seconds+60)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--seconds',type=int,default=600)
    a=p.parse_args();assert 1<=a.seconds<=1800;run(a.pid,a.seconds)
