"""Capture the installed wide169 baseline first, then the same HD flow.

Native baseline surfaces are retained at 1280x720 and reconstructed at exact
2x for comparison with 2560x1440 HD surfaces. Never call these desktop captures.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time
from PIL import Image
import wide169_trial
from wide169_trial import Session
from wide169_build import ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_identity():
    latest=json.loads((ROOT/'modernization/current-baseline.json').read_text(encoding='utf-8'))['latest_development']
    if latest['entry']!='game/Chaos-Wide169-Trial.exe':
        raise RuntimeError('The requested comparison baseline changed')
    # The launcher embeds its runtime DLL resources. Loose development DLLs
    # are not loaded by this entry and may change in another work session.
    for name in (latest['entry'],latest['engine']):
        if sha(ROOT/name)!=latest['files'][name]:
            raise RuntimeError('Baseline identity mismatch: '+name)
    installed=json.loads((ROOT/latest['installed_manifest']).read_text(encoding='utf-8'))
    if installed['status']!='installed' or sha(Path(installed['package'])/'manifest.json')!=installed['manifest_sha256']:
        raise RuntimeError('Installed package manifest changed')
    return latest


class CaptureSession(Session):
    def __init__(self,label,out,version='mixed-ui-v2',verify_baseline=True,launcher_sets_mixed=False,background_input=True):
        if label not in ('baseline','hd'):
            raise ValueError('Capture label must be baseline or hd')
        super().__init__()
        self.label=label;self.run=out/label;self.run.mkdir()
        self.hd=label=='hd';self.factor=2 if self.hd else 1
        self.lab=ROOT/('modernization/playtests/'+version+'/game-wide169' if self.hd else 'game-wide169')
        self.entry=ROOT/('modernization/playtests/'+version+'/game/Chaos-Mixed-UI-Preview.exe' if self.hd else 'game/Chaos-Wide169-Trial.exe')
        self.engine=self.lab/'Chaos-Wide169-engine.exe'
        self.records={};self.mutable={};self.original={};self.before_saves=set()
        self.snapshot_ready=False
        self.verify_baseline=verify_baseline
        self.launcher_sets_mixed=launcher_sets_mixed
        self.background_input=background_input

    def start(self):
        if any(name.startswith('chaos') for _,_,name in wide169_trial.processes(self.k)):
            raise RuntimeError('A game is running; refusing to interfere')
        if not self.hd or self.verify_baseline:
            latest=baseline_identity()
            expected=latest['files'][latest['engine']]
        else:
            expected=None
        if self.hd:
            manifest=json.loads((self.lab.parent/'manifest.json').read_text(encoding='utf-8'))
            for name,digest in manifest['files'].items():
                if sha(self.lab.parent/name)!=digest:raise RuntimeError('HD package changed: '+name)
            expected=manifest['files']['game-wide169/Chaos-Wide169-engine.exe']
        if sha(self.engine)!=expected:raise RuntimeError('Unknown engine')
        self.result['entry']=str(self.entry);self.result['engine_sha256']=expected
        self.mutable={p:(p.read_bytes(),p.stat().st_atime_ns,p.stat().st_mtime_ns)
            for p in (*sorted((self.lab/'Save').glob('*')),*sorted((self.lab/'CFG').glob('*.cfg')),
                      self.lab/'AI/EXPERIEN.DAT',self.lab/'AI/Brain.dat') if p.is_file()}
        self.before_saves=set((self.lab/'Save').glob('*'))
        # Keep a disk copy before launching: exception cleanup must never rely
        # solely on an in-memory snapshot of user saves/configuration.
        for p,(data,_,_) in self.mutable.items():
            backup=self.run/'mutable-backup'/p.relative_to(self.lab)
            backup.parent.mkdir(parents=True,exist_ok=True)
            backup.write_bytes(data)
        self.snapshot_ready=True
        env=dict(os.environ,MM_PROBE_BACKGROUND_INPUT='1')
        if not self.background_input:env.pop('MM_PROBE_BACKGROUND_INPUT',None)
        env.pop('MM_PROBE_MIXED_FONTS',None)
        if self.hd:
            if not self.launcher_sets_mixed:
                env['MM_PROBE_MIXED_RENDER']='1'
                if self.lab.parent.name in ('mixed-ui-v3','mixed-ui-v4'):env['MM_PROBE_MIXED_FONTS']='1'
        else:
            env.pop('MM_PROBE_MIXED_RENDER',None)
            wrapper=self.lab/'ddraw.dll';self.original[wrapper]=wrapper.read_bytes()
            diagnostic, diagnostic_sha = getattr(self, 'diagnostic_wrapper', (
                ROOT/'modernization/assets/hd/background-noactivate-ddraw.dll',
                '217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8'))
            if sha(diagnostic)!=diagnostic_sha:
                raise RuntimeError('Unknown background wrapper')
            wrapper.write_bytes(diagnostic.read_bytes())
        wide169_trial.LAB=self.lab
        self.proc=subprocess.Popen([str(self.entry)],cwd=self.lab,env=env)
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            ids=[pid for pid,parent,name in wide169_trial.processes(self.k)
                 if parent==self.proc.pid and name=='chaos-wide169-engine.exe']
            if ids:break
            if self.proc.poll() is not None:raise RuntimeError('Launcher exited')
            time.sleep(.2)
        else:raise RuntimeError('Owned engine missing')
        self.pid=ids[0];self.handle=self.k.OpenProcess(0x1011,False,self.pid)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        self.k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
        self.k.QueryFullProcessImageNameW.restype=W.BOOL
        size=W.DWORD(1024);path=ctypes.create_unicode_buffer(size.value)
        if not self.k.QueryFullProcessImageNameW(self.handle,0,path,ctypes.byref(size)) or Path(path.value)!=self.engine:
            raise RuntimeError('Unexpected engine process path')
        time.sleep(5)
        self.channel=self.u.RegisterWindowMessageW('MagicMayhem.Probe.BackgroundMouse.v1');self.message(0)
        self.result['surface']=[self.i(0x6a49f0),self.i(0x6a49f4)]
        if self.result['surface']!=([2560,1440] if self.hd else [1280,720]) or self.i(0x6de6fd)!=30:
            raise RuntimeError('Unexpected render geometry or frame preference')
        rect=W.RECT();self.u.GetClientRect(self.window(),ctypes.byref(rect))
        self.result['physical_client']=[rect.right,rect.bottom]
        return self

    def click_base(self,x,y,right=False):
        for event in ([0x200,0x204,0x205] if right else [0x200,0x201,0x202]):
            self.message(event,x*self.factor,y*self.factor)
            time.sleep(.09 if event in (0x201,0x204) else .04)

    def shot(self,name,move_cursor=True):
        if move_cursor:self.message(0x200,10*self.factor,700*self.factor)
        time.sleep(.15);super().capture(name+'-native')
        src=self.run/(name+'-native.png');dst=self.run/(name+'-2560x1440.png')
        with Image.open(src) as image:
            rgb=image.convert('RGB')
            if rgb.size==(1280,720):rgb=rgb.resize((2560,1440),Image.Resampling.NEAREST)
            elif rgb.size!=(2560,1440):raise RuntimeError('Unexpected capture size')
            rgb.save(dst)
        heights=[self.i(self.i(a)+16) for a in (0x6b0400,0x656680,0x6df1c0)]
        width_entry=wide169_trial.read(self.k,self.handle,0x4a58e0,12)
        width_target=struct.unpack_from('<I',width_entry,1)[0]
        translation_base=width_target-0x17e2 if width_entry[0]==0x68 and width_entry[5]==0xc3 else None
        width_values=([self.i(translation_base+rva) for rva in (0x538f0,0x538f4,0x538f8)]
            if translation_base is not None else None)
        self.records[name]={'native':str(src),'output':str(dst),'sha256':sha(dst),
            'font_heights':heights,'controls':self.controls(),
            'font_runtime_height': [self.i(a+0x220) for a in (0x6b0400,0x656680,0x6df1c0)],
            'width_entry': width_entry.hex(),'translation_base':translation_base,
            'translation_surrogate_codes':width_values,
            'font_spacing':[self.i(a+0x230) for a in (0x6b0400,0x656680,0x6df1c0)],
            'height_entry': wide169_trial.read(self.k,self.handle,0x4a6970,6).hex(),
            'unit_count':self.i(0x6def5c),'world_pointer':self.i(0x6a46bc)}
        # The global tooltip object is initialized at engine 0x5576d6 and
        # laid out by 0x4db7e0. Read its bounds without changing game state.
        tip=0x657fe8
        self.records[name]['tooltip_geometry']={
            'font':hex(self.i(tip+8)),
            'line_height':self.i(tip+0xc),
            'nominal_width':self.i(tip+0x10),
            'nominal_height':self.i(tip+0x14),
            'rect_primary':[self.i(tip+o) for o in (0x15a,0x15e,0x162,0x166)],
            'rect_secondary':[self.i(tip+o) for o in (0x16a,0x16e,0x172,0x176)],
            'text_width':self.i(tip+0x17e),
            'active':self.i(tip+4),
        }
        sprite_controls=[]
        for control in self.controls():
            if control['vtable']!='0x5c77bc':continue
            pointer=int(control['pointer'],16);sprite=self.i(pointer+0x55)
            if not sprite:continue
            table=self.i(sprite+8);data=self.i(sprite+12)
            rows=[]
            for offset in (0x59,0x5d,0x61,0x65,0x69,0x6d):
                index=self.i(pointer+offset)
                if index<0:continue
                frame=data+self.i(table+index*4)
                header=wide169_trial.read(self.k,self.handle,frame,40)
                rows.append({'field':hex(offset),'index':index,
                    'geometry':list(struct.unpack_from('<IIii',header,4)),
                    'name':header[20:28].rstrip(b'\0').decode('ascii','replace')})
            sprite_controls.append({'rect':control['rect'],'sprite':hex(sprite),
                'sprite_header':[self.i(sprite+o) for o in (0,4,8,12,16,20,24,28,32,36)],
                'frames':rows})
        self.records[name]['sprite_controls']=sprite_controls
        if name in ('grimoire','grimoire-next'):
            self.records[name]['left_tab_controls_raw']=[
                {'rect':control['rect'],'bytes':wide169_trial.read(
                    self.k,self.handle,int(control['pointer'],16),160).hex()}
                for control in self.controls() if control['vtable']=='0x5c6bd0'
                and 300*self.factor//2 <= control['rect'][0] <= 380*self.factor//2
                and 100 <= control['rect'][1] <= 260*self.factor]
        print(self.label,name,heights,flush=True)

    def load_fixture(self,name,capture_load=True):
        fixture=self.lab/'Save'/f'{name}.sav'
        if self.hd and not fixture.exists():
            source=ROOT/'modernization/playtests/mixed-ui-v3/game-wide169/Save'/f'{name}.sav'
            baseline=json.loads((ROOT/'modernization/current-baseline.json').read_text(encoding='utf-8'))
            if not source.is_file() or sha(source)!=baseline['saves'][f'{name}.sav']:
                raise RuntimeError('Missing or unverified isolated fixture: '+name)
            fixture.write_bytes(source.read_bytes())
        self.click_base(640,456);time.sleep(.7)
        controls=self.controls()
        listbox=next((c['rect'] for c in controls if c['vtable']=='0x5c6db8'),None)
        if not listbox:raise RuntimeError('Load Game list absent')
        if capture_load:self.shot('load')
        rows=sorted((self.lab/'Save').glob('*.sav'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
        n=[p.stem.lower() for p in rows].index(name)
        height=self.i(self.i(0x656680)+16)+2
        y=int(listbox[1]+(n+.5)*height)
        if y>=listbox[3]:raise RuntimeError('Fixture is outside visible load rows')
        self.message(0x200,(listbox[0]+listbox[2])//2,y)
        for event in (0x201,0x202):
            self.message(event,(listbox[0]+listbox[2])//2,y);time.sleep(.09)
        self.click_base(328,666);time.sleep(5)
        self.result['fixture_sha256']=sha(self.lab/'Save'/f'{name}.sav')
        if name in ('test2','test2-legacy'):
            base=self.i(0x6def58)
            if [self.i(base+o) for o in (8,12,16)]!=[66,48,6] or self.i(0x6def5c)!=125:
                raise RuntimeError('Wrong test2 fixture')

    def click_control(self,vtable,index=0):
        controls=[c['rect'] for c in self.controls() if c['vtable']==vtable]
        if index>=len(controls):raise RuntimeError('Expected control absent: '+vtable)
        left,top,right,bottom=controls[index]
        self.message(0x200,(left+right)//2,(top+bottom)//2)
        for event in (0x201,0x202):
            self.message(event,(left+right)//2,(top+bottom)//2);time.sleep(.09)

    def require_rect(self,rect):
        if rect not in [c['rect'] for c in self.controls()]:
            raise RuntimeError('Expected page/control rectangle absent: '+str(rect))

    def require_visible(self,name):
        # Page navigation is not accepted if only a black primary was captured.
        from PIL import ImageChops
        with Image.open(self.records[name]['native']) as im:
            red,green,blue=im.convert('RGB').split()
            histogram=ImageChops.lighter(ImageChops.lighter(red,green),blue).histogram()
        lit=sum(histogram[17:])/sum(histogram)
        self.records[name]['lit_fraction']=lit
        if lit<.12:raise RuntimeError('Page is black or nearly black: '+name)

    def __exit__(self,typ,error,tb):
        if self.handle:self.k.TerminateProcess(self.handle,0);self.k.CloseHandle(self.handle)
        if self.proc:
            try:self.proc.wait(5)
            except subprocess.TimeoutExpired:self.proc.terminate();self.proc.wait(5)
        for p,data in self.original.items():p.write_bytes(data)
        for p,(data,atime,mtime) in self.mutable.items():
            p.write_bytes(data);os.utime(p,ns=(atime,mtime))
        self.result['preserved_new_saves']=[]
        self.result['snapshot_ready']=self.snapshot_ready
        if self.snapshot_ready:
            for p in (self.lab/'Save').glob('*'):
                if p.is_file() and p not in self.before_saves:
                    # Retain unexpected saves in the runtime; they may be user
                    # data. Archive a copy rather than deleting by set difference.
                    backup=self.run/'new-saves'/p.name
                    backup.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(p,backup)
                    self.result['preserved_new_saves'].append(str(p))
        self.result['restored']=all(p.read_bytes()==data for p,data in self.original.items()) and all(
            p.read_bytes()==data for p,(data,_,_) in self.mutable.items())
        self.result['screens']=self.records
        if error:self.result['error']=str(error)
        (self.run/'capture.json').write_text(json.dumps(self.result,indent=2)+'\n',encoding='utf-8')
        if not self.result['restored']:raise RuntimeError('Diagnostic cleanup failed')


def capture_flow(label,out,flow,version,verify_baseline=True):
    with CaptureSession(label,out,version,verify_baseline=verify_baseline) as s:
        s.shot('menu')
        if flow=='portmanteau':
            s.load_fixture('test5',False);s.shot('realm-test5')
            s.require_visible('realm-test5')
            # The fourth generic button is a persistent HUD icon, not the
            # realm toolbar. Use the baseline's identified top-right box.
            if not s.hd:
                travel=[1068,4,1116,52]
                s.require_rect(travel)
            else:
                buttons=[c['rect'] for c in s.controls() if c['vtable']=='0x5c6bd0'
                         and c['rect'][1]<100 and c['rect'][0]>1800 and c['rect'][2]<=2240]
                if len(buttons)!=4:raise RuntimeError('Expected four realm toolbar buttons')
                travel=max(buttons,key=lambda r:r[0])
            s.result['checks']['travel_control_rect']=travel
            x=(travel[0]+travel[2])//2;y=(travel[1]+travel[3])//2
            for event in (0x200,0x201,0x202):
                s.message(event,x,y);time.sleep(.09 if event==0x201 else .04)
            time.sleep(1)
            opened=any(c['vtable']=='0x5c77f0' for c in s.controls())
            s.result['checks']['portmanteau_arrived']=opened
            s.shot('portmanteau-attempt')
            if opened:
                s.require_visible('portmanteau-attempt')
                for _ in range(4):
                    s.click_base(640,360);time.sleep(.25)
                s.shot('portmanteau-after-tutorial')
                if not any(c['vtable']=='0x5c77f0' for c in s.controls()):
                    raise RuntimeError('Portmanteau closed while dismissing tutorial')
                s.require_visible('portmanteau-after-tutorial')
                talisman=[c['rect'] for c in s.controls() if c['vtable']=='0x5c77bc'
                          and c['rect'][1]>=600*s.factor]
                if len(talisman)!=3:raise RuntimeError('Expected three talisman controls')
                first=min(talisman,key=lambda r:r[0])
                tx=(first[0]+first[2])//2;ty=(first[1]+first[3])//2
                s.message(0x200,tx,ty);time.sleep(.9)
                s.shot('portmanteau-talisman-hover',move_cursor=False)
                s.require_visible('portmanteau-talisman-hover')
                middle=sorted(talisman,key=lambda r:r[0])[1]
                tx=(middle[0]+middle[2])//2;ty=(middle[1]+middle[3])//2
                s.message(0x200,tx,ty);time.sleep(.9)
                s.shot('portmanteau-middle-hover',move_cursor=False)
                s.require_visible('portmanteau-middle-hover')
        elif flow=='options':
            s.click_base(640,576);time.sleep(.7);s.shot('options-before')
            s.require_visible('options-before')
            # Select the medium game speed and a middle volume point using
            # identical baseline logical coordinates in both runtimes.
            s.click_base(770,225);time.sleep(.25)
            s.click_base(400,192);time.sleep(.4);s.shot('options-after')
            s.require_visible('options-after')
            from PIL import ImageChops
            with Image.open(s.records['options-before']['output']) as first,Image.open(s.records['options-after']['output']) as second:
                d=ImageChops.difference(first.crop((550,340,2240,560)).convert('RGB'),
                                        second.crop((550,340,2240,560)).convert('RGB'))
                channels=d.split();hist=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]).histogram()
            changed=sum(hist[17:])/sum(hist)
            s.result['checks']['options_interaction_changed_fraction']=changed
            if changed<.0001:raise RuntimeError('Options interaction did not visibly change')
        elif flow=='realm-select':
            s.load_fixture('test5',False);s.shot('realm-before-selection')
            s.require_visible('realm-before-selection')
            s.click_base(760,224);time.sleep(1)
            s.shot('realm-after-selection')
            s.require_visible('realm-after-selection')
            from PIL import ImageChops
            with Image.open(s.records['realm-before-selection']['output']) as first,Image.open(s.records['realm-after-selection']['output']) as second:
                d=ImageChops.difference(first.crop((860,320,1100,590)).convert('RGB'),second.crop((860,320,1100,590)).convert('RGB'))
                channels=d.split();h=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]).histogram()
            changed=sum(h[17:])/sum(h)
            s.result['checks']['region_selection_changed_fraction']=changed
            if changed<.005:raise RuntimeError('Realm selection did not visibly change')
        elif flow in ('grimoire','grimoire-stable'):
            s.click_base(640,396);time.sleep(1)
            s.shot('realm-new-game')
            s.require_rect([x*s.factor for x in [940,30,1012,102]])
            s.require_visible('realm-new-game')
            s.click_base(976,66);time.sleep(1)
            s.shot('grimoire')
            # Grimoire close button is created at its CFG origin; sprite dimensions
            # are checked separately because they may still expose an HD defect.
            close=[c for c in s.controls() if c['vtable']=='0x5c6bd0'
                   and c['rect'][:2]==[1088*s.factor,286*s.factor]]
            if len(close)!=1:raise RuntimeError('Grimoire close control absent')
            s.require_visible('grimoire')
            s.click_base(989,650);time.sleep(.8);s.shot('grimoire-next')
            s.require_visible('grimoire-next')
            if flow=='grimoire-stable':
                time.sleep(3);s.shot('grimoire-next-t3')
                time.sleep(5);s.shot('grimoire-next-t8')
            from PIL import ImageChops
            with Image.open(s.records['grimoire']['native']) as first,Image.open(s.records['grimoire-next']['native']) as second:
                channels=ImageChops.difference(first.convert('RGB'),second.convert('RGB')).split()
                diff=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
                histogram=diff.histogram()
            changed=sum(histogram[17:])/sum(histogram)
            s.result['checks']['grimoire_turn_changed_fraction']=changed
            if changed<.01:raise RuntimeError('Grimoire turn did not change page content')
            s.click_base(1098,330);time.sleep(.7);s.shot('realm-return')
            s.require_rect([x*s.factor for x in [940,30,1012,102]])
            s.require_visible('realm-return')
        else:
            s.click_base(640,576);time.sleep(.7);s.shot('options')
            s.click_base(938,666);time.sleep(.5)
            s.load_fixture('test2-legacy' if flow=='core-tooltip' else 'test2');s.shot('battle')
            if flow=='core-tooltip':
                portrait=next((c['rect'] for c in s.controls() if c['vtable']=='0x5c6e38'),None)
                if portrait is None:raise RuntimeError('Battle portrait control absent')
                x=(portrait[0]+portrait[2])//2;y=(portrait[1]+portrait[3])//2
                # Battle controls remain 1280x720; the private wrapper channel
                # accepts output coordinates and halves them in mixed battle.
                s.message(0x200,x*s.factor,y*s.factor);time.sleep(1.5)
                s.shot('battle-tooltip',move_cursor=False)
                if not s.records['battle-tooltip']['tooltip_geometry']['active']:
                    raise RuntimeError('Battle tooltip did not appear')
            s.key(0x1b);time.sleep(.4);s.shot('escape')
            if [460,276,820,324] not in [c['rect'] for c in s.controls()]:raise RuntimeError('Esc absent')
            s.click_base(640,300);time.sleep(.7);s.shot('save')
            s.click_base(938,666);time.sleep(.4)
            if [460,276,820,324] in [c['rect'] for c in s.controls()]:s.click_base(640,480)
            time.sleep(.4);s.shot('battle-return')
            # Grimoire uses a different route in some saves; handle it as a
            # dedicated paired flow once its transition is confirmed.
        return s


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flow',choices=['core','core-tooltip','portmanteau','grimoire','grimoire-stable','realm-select','options'],default='core')
    parser.add_argument('--version',default='mixed-ui-v2')
    parser.add_argument('--baseline-comparison',type=Path,
                        help='reuse a previously verified baseline-first capture while baseline maintenance is active')
    args=parser.parse_args();ctypes.windll.user32.SetProcessDPIAware()
    out=ROOT/'modernization/assets/hd/baseline-comparisons'/str(time.time_ns());out.mkdir(parents=True)
    prior=None
    if args.baseline_comparison:
        prior=json.loads(args.baseline_comparison.read_text(encoding='utf-8'))
        if prior['flow']!=args.flow or not prior['restored'] or prior['baseline_entry']!=str(ROOT/'game/Chaos-Wide169-Trial.exe'):
            raise RuntimeError('Prior baseline capture provenance differs')
        baseline_records={name:{'output':row['baseline']} for name,row in prior['pairs'].items()}
        fixture_hash=prior['fixture_sha256']
        baseline_entry=prior['baseline_entry']
        hd=capture_flow('hd',out,args.flow,args.version,verify_baseline=False)
    else:
        baseline=capture_flow('baseline',out,args.flow,args.version)
        baseline_records=baseline.records
        fixture_hash=baseline.result.get('fixture_sha256')
        baseline_entry=str(baseline.entry)
        hd=capture_flow('hd',out,args.flow,args.version)
    if baseline_records.keys()!=hd.records.keys():
        raise RuntimeError('Flows reached different page sets')
    if fixture_hash!=hd.result.get('fixture_sha256'):
        raise RuntimeError('Comparison fixtures differ')
    pairs={}
    for name,b in baseline_records.items():
        h=hd.records[name];dest=out/(name+'-compare-5120x1440.png')
        with Image.open(b['output']) as left,Image.open(h['output']) as right:
            pair=Image.new('RGB',(5120,1440));pair.paste(left,(0,0));pair.paste(right,(2560,0));pair.save(dest)
        pairs[name]={'baseline':b['output'],'hd':h['output'],'comparison':str(dest)}
    report={'baseline_entry':baseline_entry,'hd_entry':str(hd.entry),'flow':args.flow,
        'baseline_surface':[1280,720],'hd_surface':[2560,1440],
        'baseline_output_method':'native game surface reconstructed at exact 2x nearest; native retained',
        'fixture_sha256':fixture_hash,'pairs':pairs,
        'restored':(prior['restored'] if prior else baseline.result['restored']) and hd.result['restored']}
    if prior:report['baseline_capture_source']=str(args.baseline_comparison.resolve())
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(out,flush=True)


if __name__=='__main__':main()
