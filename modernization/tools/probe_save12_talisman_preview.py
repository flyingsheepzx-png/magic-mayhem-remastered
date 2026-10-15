"""Test all talisman previews to7 with isolated low costs; no memory/save edits."""
import re,time,shutil,json
import numpy as np
from PIL import Image
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as life
from install_11_minimap_v2 import resources
from spr_assets import read_spr

def main():
 life.idle();out=c.ROOT/'modernization/logs/remastered-ui'/('save12-talisman-preview-'+str(time.time_ns()));out.mkdir()
 formal=life.DEST/life.ENTRY;fixture=life.DEST/'runtime/Save/12.sav';before=c.sha(fixture)
 cfgrel='Interface/CharacterScreen/screen (Character Screen).cfg';cfgbefore=c.sha(life.DEST/'runtime'/cfgrel)
 identity=dict(version='1.1',package=str(life.DEST),launcher_name=life.ENTRY,launcher_sha256=c.sha(formal),engine_sha256=c.ENGINES['1.1'])
 rt=c.stage(identity,out/'package',fixture);binary=c.ROOT/'modernization/build/remastered-1.1-half-stair/candidate.exe';assert resources(binary)==resources(formal)
 shutil.copy2(binary,rt.parent/life.ENTRY);identity['launcher_sha256']=c.sha(binary)
 cfg=rt/cfgrel;raw=cfg.read_bytes()
 for key,value in [('InitialCost','1'),('LinearComponent','0'),('ExponentialComponent','0')]:
  raw,n=re.subn(rb'(?m)^(Talisman_'+key.encode()+rb'\s*=)[^\r\n]*',lambda m:m[1]+value.encode(),raw);assert n==1
 cfg.write_bytes(raw)
 _,frames=read_spr(rt/'Interface/CharacterScreen/800x600/sprites.spr');dims=[(f['width'],f['height']) for f in frames[:6]]
 assert all(w==80 for w,h in dims);assert dims[:3]==dims[3:6]
 s=c.session_class()(identity,rt,out/'run',110)
 def open_page():
  toolbar=lambda x:x['vtable']=='0x5c6bd0' and x['rect'][1]<200 and x['rect'][0]>1700
  buttons=sorted(c.wait_control(s,toolbar),key=lambda x:x['rect'][0]);r=buttons[-3]['rect']
  for ev in (0x200,0x201,0x202):s.message(ev,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(.09)
  c.wait_control(s,lambda x:x['rect']==[2120,900,2192,972]);time.sleep(.3)
 def change(plus):
  for y in [936,1056,1176]:
   for ev in (0x200,0x201,0x202):s.message(ev,2156 if plus else 1940,y);time.sleep(.09)
  time.sleep(.15)
 with s:
  s.load_fixture('12');open_page();s.shot('talismans-base',False)
  for i in range(1,7):change(True);s.shot('talismans-plus'+str(i),False)
  for i in range(1,6):change(False);s.shot('talismans-minus'+str(i),False)
  change(True);s.shot('talismans-before-cancel',False)
  s.click_base(938,666);time.sleep(.4);open_page();s.shot('talismans-cancel-restored',False)
  s.click_base(938,666);time.sleep(.2)
 assert s.result['restored'] and not s.result['cleanup_errors']
 assert c.sha(fixture)==before and c.sha(life.DEST/'runtime'/cfgrel)==cfgbefore
 def image(name):return np.asarray(Image.open(s.records[name]['native']).convert('RGB'))
 base=image('talismans-base');evidence=[]
 for index,y in enumerate([876,996,1116]):
  w,h=dims[index];counts=[]
  for i in range(1,6):
   a=image('talismans-plus'+str(i));diff=np.any(a!=base,axis=2)
   slots=[int(diff[y:y+h,968+j*(w+1):968+j*(w+1)+w].sum()) for j in range(7)]
   assert all(n==0 for n in slots[:2]);assert all(n>1000 for n in slots[2:2+i]);assert all(n==0 for n in slots[2+i:]);counts.append(slots)
  # Clicking beyond7 leaves the row unchanged; subtraction removes previews.
  x=968;right=x+7*(w+1)
  assert np.array_equal(image('talismans-plus5')[y:y+h,x:right],image('talismans-plus6')[y:y+h,x:right])
  assert np.array_equal(base[y:y+h,x:right],image('talismans-minus5')[y:y+h,x:right])
  assert np.array_equal(base[y:y+h,x:right],image('talismans-cancel-restored')[y:y+h,x:right])
  for i in range(1,5):
   assert np.array_equal(image('talismans-minus'+str(i))[y:y+h,x:right],image('talismans-plus'+str(5-i))[y:y+h,x:right])
  evidence.append(dict(row=index,state_size=[w,h],preview_slot_changed_pixels=counts,max7=True,subtract_restored=True,cancel_restored=True))
 c.write_json(out/'verification.json',dict(result='passed',fixture_sha256=before,engine_sha256=identity['engine_sha256'],cost_override='isolated cfg only: initial1,linear0,exponent0; all production coefficients unchanged',rows=evidence,formal_save_unchanged=True,formal_config_unchanged=True,production_changes=False,report=str(out/'run/capture.json')))
 print(out)

if __name__=='__main__':main()
