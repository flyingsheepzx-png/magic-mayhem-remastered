"""Paired fresh-order test in the isolated terrain playtest."""
import argparse,ctypes,json,os,time,struct
from pathlib import Path
from compare_hd_baseline import CaptureSession,baseline_identity,sha,ROOT
from verify_wide169_input_map import units
from verify_hd60_runtime import read

LAB=ROOT/'modernization/playtests/terrain-diagonal-v1/game-wide169'

class Trial(CaptureSession):
    def __init__(self,out,candidate):
        super().__init__('baseline',out)
        self.lab=LAB;self.entry=LAB.parent/'game'/('Chaos-Terrain-Preview.exe' if candidate else 'Chaos-Wide169-Trial.exe')
        self.engine=LAB/'Chaos-Wide169-engine.exe'
    def start(self):
        result=super().start()
        self.result['patch']=read(self.k,self.handle,0x4f3fff,10).hex()
        return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',action='store_true')
    ap.add_argument('--save',default='test11')
    ap.add_argument('--goal',type=int,nargs=3,default=(51,71,6))
    ap.add_argument('--audit',action='store_true');args=ap.parse_args()
    baseline_identity()
    manifest=json.loads((LAB.parent/'manifest.json').read_text())
    for name,digest in manifest['files'].items():assert sha(LAB.parent/name)==digest
    out=ROOT/'modernization/logs/terrain-diagonal'/str(time.time_ns());out.mkdir(parents=True)
    prefs=LAB/'CFG/prefs.cfg';original=prefs.read_bytes();stat=prefs.stat()
    (out/'prefs.cfg').write_bytes(original)
    try:
        prefs.write_bytes(original.replace(b'PlayFMV=TRUE',b'PlayFMV=FALSE'))
        with Trial(out,args.candidate) as s:
            fixture=LAB/'Save'/(args.save+'.sav')
            assert fixture.is_file(),'Stationary fixture missing: '+str(fixture)
            s.result['fixture_sha256']=sha(fixture)
            s.click(640,456);time.sleep(.8)
            rows=sorted((LAB/'Save').glob('*.sav'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
            row=[p.stem.lower() for p in rows].index(args.save.lower());assert row<10
            s.click(640,292+row*24);time.sleep(.2);s.click(328,666)
            deadline=time.monotonic()+12
            while time.monotonic()<deadline:
                if s.i(0x6def58) and 0<s.i(0x6df180)<=s.i(0x6def5c)<=1024:break
                time.sleep(.05)
            else:raise RuntimeError('Fixture did not load')
            def initial_state():
                p=s.i(0x6def58)
                return [s.i(p+o) for o in (8,12,16,0x14,0x18,0x1c,0x618)]
            initial=initial_state();time.sleep(.6)
            assert initial==initial_state() and initial[-1]==0,'Fixture must be stationary before the target edge'
            s.result['stationary_initial']=initial
            s.key(0x5a);time.sleep(.2)
            selected=[u for u in units(s) if u['selected']]
            if [u['index'] for u in selected]!=[0]:
                s.click(1215,650);time.sleep(.2)
                selected=[u for u in units(s) if u['selected']]
            assert [u['index'] for u in selected]==[0],selected
            s.result['selected']=selected
            s.result['all_units_initial']=units(s)
            s.capture('initial')
            # One identical fresh order from the stationary user fixture.
            goals=[tuple(args.goal)]
            records=[]
            s.result['fresh_orders']=records
            for round_no,goal in enumerate(goals):
                target=None
                x,y=640,360
                attempts=[]
                for _ in range(12):
                    s.message(0x200,x,y);time.sleep(.06)
                    hit=tuple(s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64))
                    attempts.append([x,y,hit])
                    if hit==goal:target=(x,y);break
                    dx,dy,dz=[a-b for a,b in zip(goal,hit)]
                    x=max(30,min(1200,x+(dx-dy)*32));y=max(30,min(590,y+(dx+dy)*16-dz*16))
                s.result.setdefault('hover_searches',[]).append(attempts)
                if not target:raise RuntimeError('No native mouse point for '+str(goal))
                assert initial==initial_state(),'Actor moved while locating the target'
                s.click(*target,right=True)
                started=time.perf_counter();samples=[];last=None;actor_states={};actor_changes=[];captured=False
                while time.perf_counter()-started<12:
                    base=s.i(0x6def58);blob=read(s.k,s.handle,base,0xe4b)
                    val=lambda o:struct.unpack_from('<i',blob,o)[0]
                    state=dict(grid=[val(o) for o in (8,12,16)],world=[val(o) for o in (0x14,0x18,0x1c)],
                               route=blob[0x96b:0x96b+0x20c].hex(),active=val(0x618))
                    if state!=last:samples.append(dict(t=time.perf_counter()-started,**state));last=state
                    if args.audit:
                        count=s.i(0x6df180);assert 0<count<=s.i(0x6def5c)<=1024
                        table=read(s.k,s.handle,base,count*0xe4b)
                        for idx in range(count):
                            a=idx*0xe4b
                            v=lambda o:struct.unpack_from('<i',table,a+o)[0]
                            if not v(4):continue
                            g=[v(o) for o in (8,12,16)]
                            if actor_states.get(idx)!=g:
                                actor_changes.append(dict(t=round(time.perf_counter()-started,3),index=idx,id=v(0),owner=v(0x174),type=v(0xa8),grid=g))
                                actor_states[idx]=g
                        if not captured and state['grid']==[54,74,5] and time.perf_counter()-started>1.3:
                            s.capture('diagonal-midpoint');captured=True
                    if not args.audit and tuple(state['grid'])==goal and not state['active']:break
                    time.sleep(.015)
                s.capture('arrived-'+str(round_no))
                records.append(dict(goal=goal,target=target,samples=samples,actor_changes=actor_changes))
            log=LAB/'modernization/logs/terrain-diagonal.csv'
            if log.exists():(s.run/'terrain-diagonal.csv').write_bytes(log.read_bytes())
            print(out,flush=True)
    finally:
        prefs.write_bytes(original);os.utime(prefs,ns=(stat.st_atime_ns,stat.st_mtime_ns))

if __name__=='__main__':main()
