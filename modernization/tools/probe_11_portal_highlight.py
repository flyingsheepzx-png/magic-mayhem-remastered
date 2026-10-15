"""Authorized test19 hover comparison; temporary asset staging restored finally."""
import ctypes, time, os, json
import compare_remastered_ui_11 as c
import build_11_portal_highlight as fix
from install_11_minimap_v2 import idle, replace

def run():
    ctypes.windll.user32.SetProcessDPIAware();idle()
    identity=c.verify_package(c.CANDIDATE,'1.1',c.sha(c.CANDIDATE/'manifest.json'))
    v=json.loads((fix.OUT/'verification.json').read_text(encoding='utf-8'))
    out=c.ROOT/'modernization/logs/remastered-ui'/('portal-test19-'+str(time.time_ns()));out.mkdir(exist_ok=False)
    originals={fix.RT/r['path']:(fix.RT/r['path']).read_bytes() for r in v['records']}
    c.write_json(out/'asset-backup-hashes.json',{str(p):c.sha(p) for p in originals})
    results={}
    try:
        for label in ['before','after']:
            if label=='after':
                idle()
                for row in v['records']:replace(fix.RT/row['path'],(fix.OUT/row['path']).read_bytes())
            s=c.session_class()(identity,fix.RT,out/label,60)
            with s:
                now=time.time_ns();os.utime(s.lab/'Save/test19.sav',ns=(now,now))
                time.sleep(.5);s.click_base(640,456)
                deadline=time.monotonic()+4;row=None
                while time.monotonic()<deadline:
                    row=next((r for r in s.controls() if r['vtable']=='0x5c6db8'),None)
                    if row:break
                    time.sleep(.05)
                if not row:
                    c.write_json(out/'unexpected-controls.json',s.controls())
                    raise RuntimeError('load list absent')
                rect=row['rect'];h=s.i(s.i(0x656680)+16)+2
                for event in [0x200,0x201,0x202]:
                    s.message(event,(rect[0]+rect[2])//2,int(rect[1]+h/2));time.sleep(.09)
                s.click_base(328,666)
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    if any(r['pointer']=='0x659d9d' for r in s.controls()):break
                    time.sleep(.1)
                else:raise RuntimeError('test19 campaign readiness timeout')
                s.message(0x200,450,1350);time.sleep(.5)
                assert s.i(0x6f2d38)==9, 'Expected Celtic chapter portal hover'
                s.shot('portal-hover',False)
                results[label]=dict(hover_region=s.i(0x6f2d38),screenshot=s.records['portal-hover'])
                s.message(0x200,2300,1200);time.sleep(.3)
                assert s.i(0x6f2d38)==0
                s.shot('portal-inactive',False)
    finally:
        idle()
        for p,raw in originals.items():replace(p,raw)
        fix.b.verify()
    c.write_json(out/'comparison.json',results)
    print(out,flush=True)

if __name__=='__main__':run()
