"""User-authorized bounded test16 campaign UI reproduction; background only."""
import argparse,ctypes,json,os,time
from pathlib import Path
import compare_remastered_ui_11 as c

def run(name,version='1.1',extended=False):
 ctypes.windll.user32.SetProcessDPIAware()
 package=c.CANDIDATE if version=='1.1' else c.BASE;fixture=c.CANDIDATE/'runtime/Save/test16.sav'
 identity=c.verify_package(package,version,c.sha(package/('manifest.json' if version=='1.1' else 'release-manifest.json')))
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 runtime=c.stage(identity,out/'package',fixture) if version=='1.0' else package/'runtime'
 s=c.session_class()(identity,runtime,out/version,180)
 with s:
  target=s.lab/'Save'/fixture.name;stamp=time.time_ns();os.utime(target,ns=(stamp,stamp))
  s.shot('menu');s.load_fixture(fixture.stem);time.sleep(1);s.shot('loaded-test16')
  # Record opaque native surfaces and tooltip state without writing process memory.
  for tag in ['loaded-test16']:
   s.records[tag]['screen_globals']={hex(a):s.i(a) for a in [0x6e1f0c,0x6e1f20,0x6903e8,0x659f51]}
  # Dismiss only a verified standalone experience screen confirmation control.
  controls=s.controls();(out/'loaded-controls.json').write_text(json.dumps(controls,indent=2))
  toolbar=lambda x:x['vtable']=='0x5c6bd0' and x['rect'][1]<100*s.factor and x['rect'][0]>850*s.factor
  buttons=[x for x in controls if toolbar(x)]
  if not buttons:
   candidates=[x for x in controls if x['vtable']=='0x5c6c6c' and x['rect'][3]>500]
   if len(candidates)==1:
    r=candidates[0]['rect'];s.click_base((r[0]+r[2])//(2*s.factor),(r[1]+r[3])//(2*s.factor));time.sleep(1);s.shot('experience-confirmed')
  buttons=sorted(c.wait_control(s,toolbar),key=lambda x:x['rect'][0])
  s.shot('realm')
  for j,button in enumerate(buttons):
   r=button['rect'];s.message(0x200,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(1.4);s.shot('toolbar-tip-'+str(j),False)
  s.key(0x1b);time.sleep(.5);s.shot('realm-escape')
  cancels=[x for x in s.controls() if x['vtable']=='0x5c6c6c'];
  if cancels:
   r=max(cancels,key=lambda x:x['rect'][3])['rect'];s.click_base((r[0]+r[2])//(2*s.factor),(r[1]+r[3])//(2*s.factor));time.sleep(.5)
  # Character face is second-to-last toolbar entry before book and port.
  buttons=sorted(c.wait_control(s,toolbar),key=lambda x:x['rect'][0]);button=buttons[-3]
  r=button['rect'];s.click_base((r[0]+r[2])//(2*s.factor),(r[1]+r[3])//(2*s.factor));time.sleep(.6);s.shot('character')
  if extended:
   for i in range(4):s.click_base(640,360);time.sleep(.4);s.shot('character-tutorial-'+str(i))
   s.shot('character-clear')
   controls=s.controls();arrows=[x for x in controls if x['vtable']=='0x5c6bd0' and x['rect'][1]>200*s.factor and x['rect'][0]>900*s.factor]
   if len(arrows)==12:
    controls=sorted(arrows,key=lambda x:(x['rect'][1],x['rect'][0]));minus,plus=controls[:2]
    for tag,button in [('character-plus',plus),('character-minus',minus)]:
     r=button['rect'];s.click_base((r[0]+r[2])//(2*s.factor),(r[1]+r[3])//(2*s.factor));time.sleep(.3);s.shot(tag)
 c.write_json(out/'probe.json',dict(fixture_sha256=c.sha(fixture),screens=s.records,result=s.result))
 print(out/'probe.json')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--version',choices=['1.0','1.1'],default='1.1');p.add_argument('--extended',action='store_true');a=p.parse_args();run(a.name,a.version,a.extended)
