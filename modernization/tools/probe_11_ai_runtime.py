"""Opt-in bounded isolated AI trace fixture, background input/read-only sampling."""
import argparse,ctypes,json,time
import compare_remastered_ui_11 as c
from read_ai_diagnostics_11 import decode,summarize

def run(name,save,seconds):
    ctypes.windll.user32.SetProcessDPIAware()
    package=c.CANDIDATE
    identity=c.verify_package(package,'1.1',c.sha(package/'manifest.json'))
    out=c.ROOT/'modernization/logs/ai-review'/name;out.mkdir(parents=True,exist_ok=False)
    fixture=package/'runtime/Save'/f'{save}.sav'
    if not fixture.is_file():raise FileNotFoundError(fixture)
    runtime=c.stage(identity,out/'isolated-package',fixture)
    s=c.session_class()(identity,runtime,out/'session',seconds+80)
    s.launcher_args=['--ai-trace']
    with s:
        s.click_base(640,456)
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            row=next((r for r in s.controls() if r['vtable']=='0x5c6db8'),None)
            if row:break
            time.sleep(.05)
        else:raise RuntimeError('Load list did not appear')
        rect=row['rect'];h=s.i(s.i(0x656680)+16)+2
        x=(rect[0]+rect[2])//2;y=int(rect[1]+h*.5)
        for event in [0x200,0x201,0x202]:s.message(event,x,y);time.sleep(.09)
        s.click_base(328,666)
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            controls=s.controls()
            if any(r['vtable']=='0x5c6a54' and r['rect']==[0,0,1280,720] for r in controls) and s.i(0x6df180)>0:break
            time.sleep(.1)
        else:raise RuntimeError('Battle did not become ready')
        c.write_json(out/'ready.json',dict(fixture=save,sha256=c.sha(fixture),units=s.i(0x6df180),frame=s.i(0x641fbc),controls=controls))
        samples=[];deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            s.message(0)
            samples.append(dict(t=time.perf_counter(),frame=s.i(0x641fbc),units=s.i(0x6df180)))
            time.sleep(.25)
        c.write_json(out/'samples.json',samples)
        traces=list((runtime/'AI/diagnostics').glob('session-*/trace.bin'))
        assert len(traces)==1,traces
        trace=traces[0]
    # Decode after engine exit so a live partial batch is not mistaken for EOF.
    events=list(decode(trace));report=summarize(events)
    report.update(fixture=save,fixture_sha256=c.sha(fixture),trace=str(trace),trailing_bytes=(trace.stat().st_size-80)%400,scope='Isolated battle observation, no unit commands or learning-data changes to player package')
    assert report['events'].get('scheduler_begin',0)>0,report
    c.write_json(out/'trace-summary.json',report)
    c.write_json(out/'source-preserved.json',dict(files={p:c.sha(package/'runtime'/p)==v for p,v in identity['mutable_hashes'].items()}))
    print(out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--save',default='test18');p.add_argument('--seconds',type=int,default=12);a=p.parse_args()
    if not 1<=a.seconds<=60:raise ValueError('bounded observation1..60 seconds')
    run(a.name,a.save,a.seconds)
