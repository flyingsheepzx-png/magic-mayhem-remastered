"""Ordinary message-queue mouse regression in a bounded owned playtest.

Uses the real cursor only because the private channel bypasses this bug.
Restores cursor, configuration, wrapper and manifest in finally.
"""
import ctypes
import json
import shutil
import time
from ctypes import wintypes as W
from PIL import Image
from compare_hd_baseline import CaptureSession, ROOT, sha


class OrdinarySession(CaptureSession):
    def message(self,event,x=0,y=0):
        if event==0:return
        hwnd=self.window()
        if event==0x804d:
            ack=ctypes.c_size_t()
            if not self.u.SendMessageTimeoutW(hwnd,self.channel,event,0,2,2000,ctypes.byref(ack)) or ack.value!=0x4D4D4247:
                raise RuntimeError('Read-only screenshot channel failed')
            return
        self.u.ClientToScreen.argtypes=[W.HWND,ctypes.POINTER(W.POINT)]
        point=W.POINT(x,y)
        if not self.u.ClientToScreen(hwnd,ctypes.byref(point)):raise ctypes.WinError()
        self.u.SetCursorPos(point.x,point.y)
        if event!=0x200:
            self.u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
            if not self.u.PostMessageW(hwnd,event,1 if event==0x201 else 0,(y<<16)|x):raise ctypes.WinError()


def main():
    lab=ROOT/'modernization/playtests/mixed-ui-v4'
    paths=[lab/'game-wide169/ddraw.dll',lab/'game-wide169/ddraw.ini',lab/'manifest.json']
    originals={p:p.read_bytes() for p in paths}
    out=ROOT/'modernization/assets/hd/normal-mouse-probe'/str(time.time_ns());out.mkdir(parents=True)
    user=ctypes.WinDLL('user32');cursor=W.POINT();user.GetCursorPos(ctypes.byref(cursor))
    try:
        for candidate in (True,):
            paths[0].write_bytes((ROOT/'modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll').read_bytes() if candidate else originals[paths[0]])
            paths[1].write_bytes(originals[paths[1]].replace(b'devmode=false',b'devmode=true'))
            m=json.loads(originals[paths[2]])
            for p in paths[:2]:m['files'][p.relative_to(lab).as_posix()]=sha(p)
            paths[2].write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
            run=out/('candidate' if candidate else 'before');run.mkdir()
            with OrdinarySession('hd',run,'mixed-ui-v4',launcher_sets_mixed=True,background_input=False) as s:
                time.sleep(1);s.shot('menu')
                s.load_fixture('test3',False)
                s.key(0x1b);time.sleep(.5)
                for n,(x,y) in enumerate(((500,350),(1700,350),(1700,1050),(2500,700))):
                    s.message(0x200,x,y);time.sleep(.3)
                    s.shot('cursor-'+str(n),move_cursor=False)
    finally:
        for p,data in originals.items():p.write_bytes(data)
        user.SetCursorPos(cursor.x,cursor.y)
    print(out,flush=True)


if __name__=='__main__':main()
