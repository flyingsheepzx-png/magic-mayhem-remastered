"""User-authorized test17 exit-dialog background reproduction and restoration."""
import argparse,ctypes,time,os
import compare_remastered_ui_11 as c
def run(name,version):
 ctypes.windll.user32.SetProcessDPIAware()
 p=c.CANDIDATE if version=='1.1' else c.BASE;f=c.CANDIDATE/'runtime/Save/test17.sav'
 identity=c.verify_package(p,version,c.sha(p/('manifest.json' if version=='1.1' else 'release-manifest.json')))
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 runtime=c.stage(identity,out/'package',f) if version=='1.0' else p/'runtime'
 s=c.session_class()(identity,runtime,out/version,120)
 with s:
  stamp=time.time_ns();os.utime(s.lab/'Save'/f.name,ns=(stamp,stamp));s.load_fixture(f.stem);time.sleep(1);s.shot('realm')
  s.key(0x1b);time.sleep(.5);s.shot('escape');s.click_base(640,420);time.sleep(.4);s.shot('confirm')
  s.records['confirm']['dialogs']={hex(a):s.i(a) for a in [0x6e1ee4]}
  modal=[x for x in s.controls() if x['vtable']=='0x5c6d74'];assert len(modal)==1
  address=int(modal[0]['pointer'],16)
  s.records['confirm']['modal_fields']={hex(offset):s.i(address+offset) for offset in [0x25,0x29,0x3d,0x41,0x45,0x49,0x59,0x5d]}
  buttons=[x for x in s.controls() if x['pointer'] in [hex(s.i(address+0x25)),hex(s.i(address+0x29))]];assert len(buttons)==2
  no=max(buttons,key=lambda x:x['rect'][0]);r=no['rect'];s.click_base((r[0]+r[2])//(2*s.factor),(r[1]+r[3])//(2*s.factor));time.sleep(.4);s.shot('cancelled')
  assert not any(x['vtable']=='0x5c6d74' for x in s.controls())
  s.key(0x1b);time.sleep(.4);s.shot('escape-again');s.click_base(640,420);time.sleep(.4);s.shot('reopened')
  modal=[x for x in s.controls() if x['vtable']=='0x5c6d74'];assert len(modal)==1
  address=int(modal[0]['pointer'],16);yesptr=hex(s.i(address+0x25));yes=next(x for x in s.controls() if x['pointer']==yesptr)
  r=yes['rect'];s.click_base((r[0]+r[2])//(2*s.factor),(r[1]+r[3])//(2*s.factor));time.sleep(.8);s.shot('yes-result')
  s.result['checks']['no_dismisses_modal']=True
  s.result['checks']['yes_removes_modal']=not any(x['vtable']=='0x5c6d74' for x in s.controls())
 c.write_json(out/'probe.json',dict(fixture_sha256=c.sha(f),screens=s.records,result=s.result))
 print(out/'probe.json')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--version',default='1.1',choices=['1.0','1.1']);a=p.parse_args();run(a.name,a.version)
