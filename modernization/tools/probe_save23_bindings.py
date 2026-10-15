"""Isolated save23 Portmanteau binding exercise with private input/read-only state."""
import argparse,time,struct,shutil,re,json
from pathlib import Path
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read

def run(name,candidate=None):
 base.idle();out=c.ROOT/'modernization/logs/remastered-ui'/('save23-bindings-'+name);out.mkdir(exist_ok=False)
 fixture=base.DEST/'runtime/Save/23.sav';formal=base.DEST/base.ENTRY
 binary=candidate or c.ROOT/'modernization/playtests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe'
 if candidate is None:assert resources(binary)==resources(formal)
 identity=dict(version='1.1',package=str(base.DEST),launcher_name=base.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture);shutil.copy2(binary,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(binary)
 cfg=rt/'modernization/config/qol-hotkeys.json';before=cfg.read_bytes() if cfg.exists() else None
 s=c.session_class()(identity,rt,out/'run',80)
 with s:
  s.click_base(640,456);time.sleep(.7)
  box=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8');height=s.i(s.i(0x656680)+16)+2
  for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,int(box[1]+height/2));time.sleep(.09)
  s.click_base(328,666);time.sleep(2)
  controls=s.controls();c.write_json(out/'loaded-controls.json',controls);s.shot('loaded',False)
  if not any(r['vtable']=='0x5c77f0' for r in controls):
   toolbar=sorted([r for r in controls if r['vtable']=='0x5c6bd0' and r['rect'][1]<200 and 1700<r['rect'][0]<2250],key=lambda r:r['rect'][0])
   assert len(toolbar)==4,toolbar
   box=toolbar[-1]['rect']
   for ev in (0x200,0x201,0x202):s.message(ev,(box[0]+box[2])//2,(box[1]+box[3])//2);time.sleep(.09)
   time.sleep(1)
  controls=s.controls();c.write_json(out/'port-controls.json',controls)
  assert any(r['vtable']=='0x5c77f0' for r in controls)
  for _ in range(4):s.click_base(640,360);time.sleep(.2)
  s.shot('port',False)
  # Port tooltip CALL resolved to compiled module allows exact symbol telemetry.
  site=0x576d8b;raw=read(s.k,s.handle,site,5);assert raw[0]==0xe8
  lines=((candidate.parent if candidate else c.ROOT/'modernization/build/remastered-1.1-canopy-pick')/'qol_bindings.map').read_text().splitlines()
  def sym(n):return int(next(x for x in lines if '?'+n+'@' in x).split()[2],16)
  delta=site+5+struct.unpack_from('<i',raw,1)[0]-sym('port_tooltip_hook');ui=s.i(sym('port_ui')+delta)
  assert ui>0x10000
  rows=[]
  for tray in range(3):
   n=s.i(ui+0x84+tray*4);p=s.i(ui+0x218+tray*4);assert 0<=n<=21
   for index in range(n):
    control=p+index*0x86;rect=list(struct.unpack('<4i',read(s.k,s.handle,control+0x11,16)))
    rows.append(dict(tray=tray,index=index,rect=rect,item=s.i(control+0x7e)))
  c.write_json(out/'slots.json',rows);assert rows
  slot=rows[0];box=slot['rect'];s.message(0x200,(box[0]+box[2])//2,(box[1]+box[3])//2);time.sleep(.3)
  state=dict(ui=hex(ui),surface=[s.i(0x6a49f0),s.i(0x6a49f4)],mouse=[s.i(ui+0x9c),s.i(ui+0xa0)],slot=slot)
  s.key(ord('Q'));time.sleep(.3);state['after_q']=cfg.read_text(encoding='utf-8') if cfg.exists() else None
  if candidate:
   data=json.loads(state['after_q']);assert data['bindings'].get('Q')==dict(tray=slot['tray'],slot=slot['index'])
   assert not any(k!='Q' and v==data['bindings']['Q'] for k,v in data['bindings'].items())
   second=rows[1];r=second['rect'];s.message(0x200,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(.2)
   s.key(ord('Q'));time.sleep(.2);state['after_transfer']=cfg.read_text(encoding='utf-8');data=json.loads(state['after_transfer'])
   assert data['bindings']['Q']==dict(tray=second['tray'],slot=second['index'])
   s.key(0x2e);time.sleep(.2);state['after_delete']=cfg.read_text(encoding='utf-8');assert 'Q' not in json.loads(state['after_delete'])['bindings']
   state['result']='passed'
  s.shot('after-q',False);c.write_json(out/'binding.json',state)
 assert s.result['restored'] and not s.result['cleanup_errors'];print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--candidate',type=Path);a=p.parse_args();run(a.name,a.candidate)
