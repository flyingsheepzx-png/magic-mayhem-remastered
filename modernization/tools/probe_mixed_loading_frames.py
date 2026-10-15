"""Read-only high-frequency native primary capture during an owned load."""
import ctypes
import json
import threading
import time
import sys
from PIL import Image
from compare_hd_baseline import CaptureSession, ROOT, sha
from wide169_trial import read
from ctypes import wintypes as W


def main():
    lab = ROOT / 'modernization/playtests/mixed-ui-v4'
    wrapper = lab / 'game-wide169/ddraw.dll'
    manifest = lab / 'manifest.json'
    original = wrapper.read_bytes(), manifest.read_bytes()
    out = ROOT / 'modernization/assets/hd/loading-frames' / str(time.time_ns())
    out.mkdir(parents=True)
    created_save=None
    created_hash=None
    try:
        wrapper.write_bytes((ROOT / 'modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll').read_bytes())
        m = json.loads(original[1]); m['files']['game-wide169/ddraw.dll'] = sha(wrapper)
        manifest.write_text(json.dumps(m, indent=2) + '\n', encoding='utf-8')
        with CaptureSession('hd', out, 'mixed-ui-v4', launcher_sets_mixed=True) as s:
            saving='--save' in sys.argv
            if saving:
                created_save=s.lab/'Save/hdpgtest.sav'
                if created_save.exists():raise RuntimeError('Owned save name already exists')
                s.load_fixture('test2-legacy',False);s.key(0x1b);time.sleep(.4)
                s.click_base(640,300);time.sleep(.6)
                s.message(0x200,1200,410)
                for event in (0x201,0x202):s.message(event,1200,410);time.sleep(.09)
                for _ in range(30):s.key(8)
                s.u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
                for ch in 'hdpgtest':s.u.PostMessageW(s.window(),0x102,ord(ch),0);time.sleep(.05)
                s.shot('save-name')
            else:
                s.click_base(640,456); time.sleep(.7)
                box = next(c['rect'] for c in s.controls() if c['vtable']=='0x5c6db8')
                rows = sorted((s.lab/'Save').glob('*.sav'), key=lambda p:p.stat().st_mtime_ns, reverse=True)
                n = [p.stem.lower() for p in rows].index(sys.argv[1] if len(sys.argv)>1 else 'test3')
                y = int(box[1]+(n+.5)*(s.i(s.i(0x656680)+16)+2))
                for event in (0x200,0x201,0x202):
                    s.message(event,(box[0]+box[2])//2,y); time.sleep(.09)
            def query(event):
                ack=ctypes.c_size_t()
                if not s.u.SendMessageTimeoutW(s.window(),s.channel,event,0,2,2000,ctypes.byref(ack)):
                    raise RuntimeError('Surface telemetry failed')
                return ack.value
            pointer, pitch = query(0x8050), query(0x8051)
            if not pointer or pitch != 5120: raise RuntimeError('Unexpected primary')
            stop = threading.Event(); frames=[]; errors=[]
            def sample():
                try:
                    while not stop.is_set() and len(frames)<100:
                        start=time.monotonic()
                        pixels=read(s.k,s.handle,pointer,pitch*1440)
                        frames.append((start,pixels,s.i(0x642c68)))
                        time.sleep(.04)
                except Exception as e: errors.append(str(e))
            thread=threading.Thread(target=sample);thread.start()
            try:
                s.click_base(328,666);time.sleep(4)
                if saving:
                    if not created_save.is_file():raise RuntimeError('Save action failed')
                    created_hash=sha(created_save)
            finally:
                stop.set();thread.join()
            report=[]
            for n,(t,pixels,count) in enumerate(frames):
                im=Image.frombytes('RGB',(2560,1440),pixels,'raw','BGR;16',pitch,1)
                path=out/f'frame-{n:03}.png';im.save(path)
                report.append({'frame':n,'time':t,'controls':count,'path':str(path)})
            (out/'frames.json').write_text(json.dumps({'frames':report,'errors':errors},indent=2),encoding='utf-8')
            print(out,flush=True)
    finally:
        wrapper.write_bytes(original[0]);manifest.write_bytes(original[1])
        if created_save and created_hash and created_save.is_file():
            if sha(created_save)!=created_hash:raise RuntimeError('Owned diagnostic save changed; preserved')
            created_save.unlink()


if __name__=='__main__':main()
