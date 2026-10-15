"""Scoped test17 Forest of Pain hover with original save/state restoration."""
import argparse,ctypes,time,os
import compare_remastered_ui_11 as c
def run(name):
 ctypes.windll.user32.SetProcessDPIAware();p=c.CANDIDATE;f=p/'runtime/Save/test17.sav'
 identity=c.verify_package(p,'1.1',c.sha(p/'manifest.json'));out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 s=c.session_class()(identity,p/'runtime',out/'1.1',120)
 with s:
  stamp=time.time_ns();os.utime(s.lab/'Save'/f.name,ns=(stamp,stamp));s.load_fixture(f.stem);time.sleep(.8);s.shot('plain')
  for name,x,y in [('forest',900,550),('forest-center',830,500),('forest-edge',850,625)]:
   s.message(0x200,x*2,y*2);time.sleep(.7);s.shot(name,False)
  s.message(0x200,20,1400);time.sleep(.5);s.shot('unhover')
 c.write_json(out/'probe.json',dict(fixture_sha256=c.sha(f),screens=s.records,result=s.result));print(out/'probe.json')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();run(a.name)
