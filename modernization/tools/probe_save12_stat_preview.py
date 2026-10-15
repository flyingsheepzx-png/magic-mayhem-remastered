"""User-authorized save12 stat previews, reversible isolated UI interaction."""
import argparse,time,struct,shutil,json
from pathlib import Path
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as life
from install_11_minimap_v2 import resources
from verify_hd60_runtime import read

def run(name,assetdir=None):
 life.idle();out=c.ROOT/'modernization/logs/remastered-ui'/('save12-stat-preview-'+name);out.mkdir(exist_ok=False)
 formal=life.DEST/life.ENTRY;fixture=life.DEST/'runtime/Save/12.sav'
 identity=dict(version='1.1',package=str(life.DEST),launcher_name=life.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture)
 binary=c.ROOT/'modernization/build/remastered-1.1-half-stair/candidate.exe';assert resources(binary)==resources(formal)
 shutil.copy2(binary,rt.parent/life.ENTRY);identity['launcher_sha256']=c.sha(binary)
 if assetdir:
  for p in assetdir.glob('*.PNG'):shutil.copy2(p,rt/'Interface/CharacterScreen/800x600'/p.name)
 s=c.session_class()(identity,rt,out/'run',100)
 with s:
  s.load_fixture('12');toolbar=lambda x:x['vtable']=='0x5c6bd0' and x['rect'][1]<200 and x['rect'][0]>1700
  buttons=sorted(c.wait_control(s,toolbar),key=lambda x:x['rect'][0]);r=buttons[-3]['rect']
  for ev in (0x200,0x201,0x202):s.message(ev,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(.09)
  time.sleep(.5);s.shot('character-initial',False)
  controls=s.controls();c.write_json(out/'controls.json',controls)
  snapshots=[]
  for label in ['initial','plus1','plus2','plus3']:
   if label!='initial':
    for rect in [[2120,540,2192,612],[2120,660,2192,732],[2120,780,2192,852]]:
     assert any(x['rect']==rect for x in controls)
     for ev in (0x200,0x201,0x202):s.message(ev,(rect[0]+rect[2])//2,(rect[1]+rect[3])//2);time.sleep(.09)
    time.sleep(.2)
   s.shot('character-'+label,False)
   rows=[]
   for control in controls:
    r=control['rect']
    if r[0]==968 and r[2]==1808:
     address=int(control['pointer'],16);blob=read(s.k,s.handle,address,0x200)
     (out/('control-'+label+'-'+str(control['index'])+'.bin')).write_bytes(blob)
     rows.append(dict(control=control,dwords=[struct.unpack_from('<I',blob,o)[0] for o in range(0,0x100,4)]))
   snapshots.append(dict(label=label,rows=rows))
  c.write_json(out/'bar-state.json',snapshots)
  # Cancel the preview; never commit points to player or fixture saves.
  s.click_base(938,666);time.sleep(.3)
 assert s.result['restored'] and not s.result['cleanup_errors'];print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--assets',type=Path);args=p.parse_args();run(args.name,args.assets)
