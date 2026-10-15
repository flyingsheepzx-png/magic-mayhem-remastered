"""Owned-process background verification of the independent widescreen runtime."""
from pathlib import Path
import os,sys,json,time,shutil,ctypes,subprocess,argparse,hashlib
from ctypes import wintypes as W
from PIL import Image
from verify_hd60_runtime import configured_kernel,processes,read,HOOKS
from wide169_build import ROOT,GAME,LAB,BUILD,sha,write_json

def runtime_files(folder):
    # Do not traverse the modernization compatibility junction or screenshots.
    for root,dirs,files in os.walk(folder,followlinks=False):
        dirs[:]=[d for d in dirs if d not in ('modernization','ss')]
        for name in files:yield Path(root)/name

class Session:
    def __init__(self):
        self.k=configured_kernel();self.u=ctypes.WinDLL('user32',use_last_error=True)
        self.u.GetForegroundWindow.restype=W.HWND
        self.u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
        self.u.GetClientRect.argtypes=[W.HWND,ctypes.POINTER(W.RECT)]
        self.u.RegisterWindowMessageW.argtypes=[W.LPCWSTR]
        self.u.SendMessageTimeoutW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM,W.UINT,W.UINT,ctypes.POINTER(ctypes.c_size_t)]
        self.u.SendMessageTimeoutW.restype=ctypes.c_size_t
        self.cb=ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
        self.u.EnumWindows.argtypes=[self.cb,W.LPARAM]
        self.u.IsWindowVisible.argtypes=[W.HWND]
        self.run=ROOT/'modernization/logs/wide169'/str(time.time_ns());self.run.mkdir(parents=True)
        self.result=dict(status='started',screenshots={},checks={})
        self.proc=None;self.handle=None;self.original={}
    def __enter__(self):
        try:return self.start()
        except BaseException:
            self.__exit__(*sys.exc_info());raise
    def start(self):
        if any(name.startswith('chaos') for _,_,name in processes(self.k)):raise RuntimeError('Game already running')
        self.before={str(p):sha(p.read_bytes()) for folder in (GAME,LAB) for p in runtime_files(folder)}
        # Gameplay legitimately updates these files. Preserve the fixture bytes,
        # restore them after the owned process exits, then audit the whole runtime.
        self.mutable={p:(p.read_bytes(),p.stat().st_atime_ns,p.stat().st_mtime_ns) for p in (LAB/'AI/EXPERIEN.DAT',LAB/'AI/Brain.dat',*sorted((LAB/'Save').glob('*')),*sorted((LAB/'CFG').glob('*.cfg')))
                      if p.is_file()}
        # Keep the accepted runtime unchanged; only the isolated wrapper is temporary.
        p=LAB/'ddraw.dll';self.original[p]=p.read_bytes()
        diagnostic=ROOT/'modernization/assets/hd/background-noactivate-ddraw.dll'
        if sha(diagnostic.read_bytes())!='217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8':raise RuntimeError('Unknown diagnostic wrapper')
        p.write_bytes(diagnostic.read_bytes())
        for p,data in self.original.items():(self.run/p.name).write_bytes(data)
        entry=Path(os.environ.get('MM_WIDE169_DIAGNOSTIC_LAUNCHER',str(GAME/'Chaos-Wide169-Trial.exe')))
        if entry.parent.resolve()!=GAME.resolve() or not entry.name.startswith('Chaos-Wide169-'):
            raise RuntimeError('Diagnostic launcher path outside expected game root')
        self.proc=subprocess.Popen([str(entry)],cwd=LAB,
             env=dict(os.environ,MM_PROBE_BACKGROUND_INPUT='1',MM_PROBE_RENDER_LIGHT_LOG='1'))
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            ids=[pid for pid,parent,name in processes(self.k) if parent==self.proc.pid and name=='chaos-wide169-engine.exe']
            if ids:break
            time.sleep(.15)
        else:raise RuntimeError('Missing owned engine')
        self.pid=ids[0];self.handle=self.k.OpenProcess(0x1011,False,self.pid)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        self.result['pid']=self.pid
        identity=json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']
        expected=identity['files']['game-wide169/Chaos-Wide169-engine.exe']
        if sha((LAB/'Chaos-Wide169-engine.exe').read_bytes())!=expected:raise RuntimeError('Engine identity mismatch')
        self.result['engine_sha256']=expected
        time.sleep(4)
        self.channel=self.u.RegisterWindowMessageW('MagicMayhem.Probe.BackgroundMouse.v1')
        self.message(0)
        self.result['checks']['hooks']={hex(a):read(self.k,self.handle,a,1)==b'\xe9' for a in HOOKS}
        self.result['checks']['surface']=[self.i(0x6a49f0),self.i(0x6a49f4)]
        self.result['checks']['fps_preference']=self.i(0x6de6fd)
        rect=W.RECT();self.u.GetClientRect(self.window(),ctypes.byref(rect));self.result['checks']['output_client']=[rect.right,rect.bottom]
        output=self.result['checks']['output_client']
        diagnostic_native=os.environ.get('MM_ALLOW_NATIVE_CLIENT')=='1' and output==[1280,720]
        diagnostic_scaled=os.environ.get('MM_ALLOW_SCALED_CLIENT')=='1' and output[0]>=1280 and output[1]>=720 and output[0]*9==output[1]*16
        self.result['checks']['native_client_diagnostic']=diagnostic_native
        self.result['checks']['scaled_client_diagnostic']=diagnostic_scaled
        if not all(self.result['checks']['hooks'].values()) or self.result['checks']['surface']!=[1280,720] or self.result['checks']['fps_preference']!=30 or (output!=[2560,1440] and not diagnostic_native and not diagnostic_scaled):raise RuntimeError('Startup geometry/hook gate failed')
        self.message(0x200,640,360)
        self.capture('menu');return self
    def window(self):
        found=[]
        def each(hwnd,_):
            pid=W.DWORD();self.u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value==self.pid and self.u.IsWindowVisible(hwnd):found.append(hwnd)
            return True
        self.u.EnumWindows(self.cb(each),0)
        if len(found)!=1:
            details=[]
            self.u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int]
            for hwnd in found:
                rect=W.RECT();self.u.GetClientRect(hwnd,ctypes.byref(rect))
                title=ctypes.create_unicode_buffer(256);self.u.GetWindowTextW(hwnd,title,len(title))
                children=[]
                def child(ch,_):
                    buf=ctypes.create_unicode_buffer(1024);self.u.GetWindowTextW(ch,buf,len(buf))
                    if buf.value:children.append(buf.value)
                    return True
                self.u.EnumChildWindows.argtypes=[W.HWND,self.cb,W.LPARAM]
                self.u.EnumChildWindows(hwnd,self.cb(child),0)
                details.append(dict(hwnd=hwnd,title=title.value,client=[rect.right,rect.bottom],children=children))
            raise RuntimeError(f'Expected one owned window: {details}')
        return found[0]
    def i(self,addr):return int.from_bytes(read(self.k,self.handle,addr,4),'little',signed=True)
    def message(self,event,x=0,y=0):
        ack=ctypes.c_size_t()
        if not self.u.SendMessageTimeoutW(self.window(),self.channel,event,(y<<16)|x,2,2000,ctypes.byref(ack)) or ack.value!=0x4D4D4247:raise RuntimeError('Private input failed')
    def click(self,x,y,right=False):
        if not 0<=x<1280 or not 0<=y<720:raise ValueError('Native coordinate out of bounds')
        for event in ([0x200,0x204,0x205] if right else [0x200,0x201,0x202]):
            self.message(event,x,y);time.sleep(.09 if event in (0x201,0x204) else .04)
    def key(self,key):
        self.u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
        self.u.PostMessageW(self.window(),0x100,key,0);time.sleep(.1);self.u.PostMessageW(self.window(),0x101,key,0)
    def capture(self,name):
        # Wrapper filenames have one-second precision; avoid collisions.
        elapsed=time.monotonic()-getattr(self,'last_capture',0)
        if elapsed<1.1:time.sleep(1.1-elapsed)
        before=set((LAB/'ss').glob('*.png'));self.message(0x804d);self.last_capture=time.monotonic();time.sleep(.2)
        files=set((LAB/'ss').glob('*.png'))-before
        if len(files)!=1:raise RuntimeError('No unique screenshot')
        target=self.run/(name+'.png');shutil.copy2(files.pop(),target)
        self.result['screenshots'][name]=str(target)
        with Image.open(target) as im:
            rgb=im.convert('RGB'); bars=list(rgb.crop((0,0,160,720)).get_flattened_data())+list(rgb.crop((1120,0,1280,720)).get_flattened_data())
            self.result.setdefault('images',{})[name]=dict(size=list(im.size),bar_nonblack_fraction=sum(max(p)>8 for p in bars)/len(bars))
    def controls(self):
        rows=[];count=self.i(0x642c68)
        if not 0<=count<=400:raise RuntimeError('Control count')
        for n in range(count):
            p=self.i(0x642034+4*n)
            if not p:continue
            try:rect=[self.i(p+o) for o in (0x11,0x15,0x19,0x1d)]
            except OSError:continue
            rows.append(dict(index=n,pointer=hex(p),vtable=hex(self.i(p)),rect=rect))
        return rows
    def bars(self,name):
        if self.result['images'][name]['bar_nonblack_fraction']!=0:raise RuntimeError('Nonblack side bar: '+name)
    def switch_window(self):
        hwnd=self.window();self.u.ShowWindow.argtypes=[W.HWND,ctypes.c_int]
        self.u.ShowWindow(hwnd,6);time.sleep(.3);self.u.ShowWindow(hwnd,4);time.sleep(.5)
        self.message(0);self.capture('window-restored')
        self.result['checks']['minimize_restore']=True
    def audio(self):
        sys.path.insert(0,str(BUILD/'python-deps'))
        from pycaw.pycaw import AudioUtilities
        from pycaw.api.endpointvolume import IAudioMeterInformation
        peaks=[]
        for _ in range(20):
            owned=[a for a in AudioUtilities.GetAllSessions() if a.ProcessId==self.pid]
            for a in owned:
                meter=a._ctl.QueryInterface(IAudioMeterInformation);peaks.append(float(meter.GetPeakValue()))
            time.sleep(.15)
        self.result['checks']['audio']=dict(owned_session_samples=len(peaks),max_peak=max(peaks,default=0))
        if not peaks or max(peaks)<=0:raise RuntimeError('No owned audible audio session')
    def load(self,name):
        self.click(640,456);time.sleep(1);self.capture('load')
        rows=sorted((LAB/'Save').glob('*.sav'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
        n=[p.stem.lower() for p in rows].index(name)
        self.result['save_row']=n
        self.click(640,292+n*24);time.sleep(.3)
        self.click(328,666);time.sleep(5);self.capture(name)
        self.result['controls']=self.controls()
    def __exit__(self,typ,error,tb):
        if self.handle:self.k.TerminateProcess(self.handle,0);self.k.CloseHandle(self.handle)
        if self.proc:
            try:self.proc.wait(5)
            except subprocess.TimeoutExpired:self.proc.terminate();self.proc.wait(5)
        for p,data in self.original.items():p.write_bytes(data)
        for p,(data,atime,mtime) in getattr(self,'mutable',{}).items():
            p.write_bytes(data);os.utime(p,ns=(atime,mtime))
        # A save may be added by the user or another session during this run.
        # Never delete an unfamiliar save as part of fixture cleanup.
        self.result['changed_protected']=[p for p,h in getattr(self,'before',{}).items() if not Path(p).exists() or sha(Path(p).read_bytes())!=h]
        after={str(p) for folder in (GAME,LAB) for p in runtime_files(folder)}
        self.result['changed_protected']+=sorted(after-set(getattr(self,'before',{})))
        self.result['status']='failed' if error or self.result['changed_protected'] else 'completed'
        if error:self.result['error']=str(error)
        write_json(self.run/'result.json',self.result)
        print(self.run/'result.json')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('flow',choices=['menu','test2','test5','grimoire','save','realm','media','intro','esc','qol']);args=parser.parse_args()
    with Session() as s:
        if args.flow in ('esc','qol'):
            sites={0x578610:0xe9,0x58bf40:0xe9,0x46c194:0xe9,0x509ca6:0xe9,0x4fdad0:0xe9,0x4a54cf:0xe8}
            s.result['checks']['qol_hooks']={hex(a):read(s.k,s.handle,a,1)==bytes([op]) for a,op in sites.items()}
            if not all(s.result['checks']['qol_hooks'].values()):raise RuntimeError('QoL hook gate failed')
        if args.flow=='esc':
            s.load('test2');s.key(0x1b);time.sleep(.5);s.capture('esc-centered')
            s.result['esc_controls']=s.controls()
            code=read(s.k,s.handle,0x5c4350,10)
            if code!=bytes.fromhex('b818010000b978000000'):raise RuntimeError('Esc draw origin mismatch')
            s.result['checks']['esc_background_origin']=[280,120]
            s.click(640,480);time.sleep(.5);s.capture('esc-dismissed')
            if any(c['rect']==[460,456,820,504] for c in s.controls()):raise RuntimeError('Esc cancel control still present')
            if Image.open(s.run/'esc-centered.png').tobytes()==Image.open(s.run/'esc-dismissed.png').tobytes():raise RuntimeError('Esc cancel did not dismiss')
            s.result['checks']['esc_cancel_hit']=True
        if args.flow=='qol':
            s.load('test7');s.key(0x5a);time.sleep(.3)
            box=0x6a2dd0;checks=[]
            for key,icon in [('Q',0),('W',2),('E',3),('R',1)]:
                s.key(ord(key));time.sleep(.25)
                state=[s.i(box+0x1908),s.i(0x6903e8),s.i(0x6e984c)]
                if state!=[icon,2,1]:raise RuntimeError('QoL targeting mismatch '+key+str(state))
                s.click(640,360,True);time.sleep(.25)
                cancelled=[s.i(box+0x1908),s.i(0x6903e8),s.i(0x6e984c)]
                if cancelled!=[-1,1,1]:raise RuntimeError('QoL cancel mismatch '+key+str(cancelled))
                checks.append(dict(key=key,target=state,cancel=cancelled))
            s.result['checks']['qol_target_cancel']=checks;s.capture('qol-battle')
        if args.flow in ('test2','test5'):s.load(args.flow)
        if args.flow=='save':s.load('test5')
        if args.flow=='realm':
            s.load('test5');s.result['realm_id_before']=s.i(0x659f51)
            s.click(760,224);time.sleep(1);s.capture('region-selected');s.bars('region-selected')
            s.result['realm_id_after']=s.i(0x659f51)
            before=Image.open(s.run/'test5.png').crop((430,160,550,295)).tobytes()
            after=Image.open(s.run/'region-selected.png').crop((430,160,550,295)).tobytes()
            if before==after:raise RuntimeError('Realm marker selection did not change')
            s.result['selected_region_controls']=s.controls()
        if args.flow=='intro':
            s.click(640,396)
            for n in range(3):time.sleep(1);s.capture('new-game-'+str(n))
        if args.flow=='media':
            s.audio();s.click(640,396);time.sleep(.5);s.click(380,645)
            for n in range(5):time.sleep(1);s.capture('entry-'+str(n))
            s.audio()
        if args.flow=='test2':
            table=s.i(0x6def58);s.result['unit0']=[s.i(table+o) for o in (8,12,16)]
            s.result['scene_rect']=[s.i(s.i(0x6c482c)+o) for o in (0,4,8,12)]
            if s.result['unit0']!=[66,48,6] or s.i(0x6def5c)!=125:raise RuntimeError('Wrong test2 fixture')
            def camera():return [s.i(0x689930+o) for o in (0x39,0x3d,0x41,0x45,0x49,0x4d)]
            s.click(1218,650);time.sleep(.5);s.capture('selected')
            with Image.open(s.run/'selected.png') as im:
                corners=[(620,298),(621,298),(663,298),(664,298),(620,370),(621,370),(663,370),(664,370)]
                count=sum((p:=im.getpixel(pt))[0]>150 and p[1]>140 and p[2]<80 for pt in corners)
            s.result['selection_corner_pixels']=count
            if count<6:raise RuntimeError('Selection not confirmed; movement withheld')
            s.click(1170,360,True);time.sleep(5);s.capture('moved')
            s.result['movement']=[s.i(table+o) for o in (8,12,16)]
            if s.result['movement']==s.result['unit0']:raise RuntimeError('No unit movement')
            roof=s.i(0x689995);s.click(1130,648);time.sleep(.3);changed=s.i(0x689995);s.click(1130,648);time.sleep(.3)
            s.result['roof']=[roof,changed,s.i(0x689995)]
            if roof==changed or s.i(0x689995)!=roof:raise RuntimeError('Roof toggle failed')
            scroll=[]
            for name,x,y,direction in [('right',1279,360,7),('left',0,360,9),('bottom',640,719,8),('top',640,0,6)]:
                s.message(0x200,640,360);time.sleep(.2);before=camera()
                for _ in range(20):s.message(0x200,x,y);time.sleep(.05)
                after=camera();actual=s.i(0x5e1740)
                scroll.append(dict(edge=name,before=before,after=after,direction=actual,passed=before!=after and actual==direction))
            s.result['scroll']=scroll
            if not all(r['passed'] for r in scroll):raise RuntimeError('Four-edge scroll failed')
            s.message(0x200,640,360);s.capture('scroll-complete')
        if args.flow=='test5':
            for name,x,y in [('portmanteau',1090,30),('dismiss',640,360),('character',934,43)]:
                s.click(x,y);time.sleep(1.3);s.capture(name)
                s.result[name+'_controls']=s.controls()
            s.bars('test5');s.bars('portmanteau');s.bars('character')
            with Image.open(s.run/'character.png') as im:
                checks={}
                for name,y,c in [('law',468,2),('neutral',528,1),('chaos',588,0)]:
                    points=[(x,yy) for yy in range(y-22,y+22) for x in range(480,526)
                            if (v:=im.getpixel((x,yy)))[c]>60 and v[c]>max(v[k] for k in range(3) if k!=c)*1.4]
                    if len(points)<200 or max(yy for x,yy in points)-min(yy for x,yy in points)<26:raise RuntimeError('Incomplete talisman '+name)
                    checks[name]=dict(pixels=len(points),rows=max(yy for x,yy in points)-min(yy for x,yy in points)+1)
                s.result['checks']['talismans']=checks
            for name,y in [('law',468),('neutral',528),('chaos',588)]:
                s.capture(name+'-before');s.click(1078,y);time.sleep(.3);s.capture(name+'-after')
                a=Image.open(s.run/(name+'-before.png')).crop((988,y-28,1060,y+28))
                b=Image.open(s.run/(name+'-after.png')).crop((988,y-28,1060,y+28))
                if a.tobytes()==b.tobytes():raise RuntimeError('Talisman + hit failed '+name)
                s.click(970,y);time.sleep(.2)
            s.click(930,660);time.sleep(.6);s.capture('character-cancel');s.bars('character-cancel')
            s.switch_window()
        if args.flow=='grimoire':
            s.click(640,396);time.sleep(1);s.capture('region')
            s.click(976,66);time.sleep(1);s.capture('grimoire')
            s.bars('menu');s.bars('region');s.bars('grimoire')
            s.click(305,176);time.sleep(1);s.capture('grimoire-portmanteau-page');s.bars('grimoire-portmanteau-page')
            if Image.open(s.run/'grimoire.png').tobytes()==Image.open(s.run/'grimoire-portmanteau-page.png').tobytes():raise RuntimeError('Grimoire page navigation did not change')
        if args.flow=='save':
            s.key(0x1b);time.sleep(.6);s.capture('mini-menu')
            s.click(640,300);time.sleep(.7);s.capture('save-dialog')
            s.click(640,203)
            for _ in range(40):s.key(8)
            for ch in 'wide169check':s.u.PostMessageW(s.window(),0x102,ord(ch),0);time.sleep(.08)
            s.click(330,666);time.sleep(1.5);s.capture('saved')
            saved=LAB/'Save/wide169check.sav'
            if not saved.exists() or saved.stat().st_size<1000:raise RuntimeError('Save file absent')
            s.result['checks']['saved_sha256']=sha(saved.read_bytes())
            s.key(0x1b);time.sleep(.5);s.click(640,240);time.sleep(.6);s.capture('reload-dialog')
            s.click(640,292);s.click(328,666);time.sleep(4);s.capture('reloaded')
            s.bars('save-dialog');s.bars('reloaded')
            s.result['checks']['save_reload']=True
if __name__=='__main__':main()
