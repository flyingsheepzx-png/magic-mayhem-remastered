"""CPU-only six-state SR comparison/SPR candidates; never writes runtime files."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
from spr_assets import read_spr,decode
from stage_mixed_ui_v3_sprites import encode
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'modernization/assets/hd/quality-review-1.1/community-sr-20260930'
if (ROOT/'modernization/assets/hd/seedvr2-ui-1.1/plan.json').exists():raise RuntimeError('Historical SR review retired; inspect SeedVR2 production instead')
OLD=OUT.parent/'ui-icons-20260930'
CURRENT=ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Sprites/Buttons.spr'
SOURCE=ROOT/'modernization/assets/hd/source-original/Sprites/Buttons.spr'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((OLD/'review-metrics.json').read_text(encoding='utf-8'))
assert sha(CURRENT)==report['inputs']['current']['sha256'] and sha(SOURCE)==report['inputs']['source']['sha256']
cp,cf=read_spr(CURRENT);sp,sf=read_spr(SOURCE);qp,qf=read_spr(OLD/'Buttons-qwen-trial.spr')
boxes=json.loads((OUT/'atlas.json').read_text(encoding='utf-8'))
assert not cp and len(cf)==21
methods={};checks={};state_metrics={}
for name in ['seedvr','pixelperfect']:
 atlas=Image.open(OUT/(name+'-atlas-4x.png')).convert('RGB');assert atlas.size==(1024,768)
 ims={};payloads=[f['data'] for f in cf]
 for row in boxes:
  i=row['frame'];box=[x*4 for x in row['rect']];size=(cf[i]['width'],cf[i]['height'])
  im=atlas.crop(box).resize(size,Image.Resampling.LANCZOS).convert('RGBA')
  im.putalpha(decode(sp,sf[i]).getchannel('A').resize(size,Image.Resampling.NEAREST))
  raw=bytearray(encode(cf[i],im));struct.pack_into('<2i',raw,12,*cf[i]['offset']);payloads[i]=bytes(raw);ims[i]=im
  folder=OUT/name;folder.mkdir(exist_ok=True);im.save(folder/f'{i:02d}.png')
 raw=bytearray(CURRENT.read_bytes()[:24]);pos=0
 for block in payloads:raw.extend(struct.pack('<I',pos));pos+=len(block)
 for block in payloads:raw.extend(block)
 struct.pack_into('<I',raw,4,len(raw));dest=OUT/('Buttons-'+name+'-six-state-trial.spr');dest.write_bytes(raw)
 p,frames=read_spr(dest);rows=[]
 for i,(a,b) in enumerate(zip(cf,frames)):
  assert all(a[k]==b[k] for k in ['width','height','offset','name','flags'])
  actual=np.array(decode(p,b));current=np.array(decode(cp,a));assert np.array_equal(actual[:,:,3],current[:,:,3])
  if i not in ims:assert a['data']==b['data']
  else:
   wanted=np.array(ims[i]);mask=wanted[:,:,3]>0;assert np.abs(actual[:,:,:3].astype(int)-wanted[:,:,:3].astype(int))[mask].max()<=9
  rows.append(dict(frame=i,metadata_exact=True,alpha_exact=True,unmodified_payload_exact=i not in ims))
 methods[name]=ims;checks[name]=dict(sprite=str(dest),sha256=sha(dest),checks=rows)
 # Preserve the brighter pressed-state flash as well as its native shorter box.
 state_metrics[name]={}
 for motif,i in [('book',3),('chest',6)]:
  a=np.array(ims[i]);b=np.array(ims[i+2]);h=min(a.shape[0],b.shape[0]);mask=(a[:h,:,3]>0)&(b[:h,:,3]>0)
  delta=float((b[:h,:,:3].mean(2)-a[:h,:,:3].mean(2))[mask].mean())
  assert delta>0,(name,motif,delta)
  state_metrics[name][motif]=dict(pressed_mean_rgb_delta=delta)
names=['Lanczos','Current','Qwen sheet','SeedVR2','PixelPerfectV4'];canvas=Image.new('RGB',(1000,780),'#303038');d=ImageDraw.Draw(canvas)
for col,name in enumerate(names):d.text((col*200+20,12),name,fill='white')
for row,i in enumerate(range(3,9)):
 size=(cf[i]['width'],cf[i]['height']);orig=decode(sp,sf[i]);lanczos=orig.resize(size,Image.Resampling.LANCZOS);lanczos.putalpha(orig.getchannel('A').resize(size,Image.Resampling.NEAREST))
 for col,im in enumerate([lanczos,decode(cp,cf[i]),decode(qp,qf[i]),methods['seedvr'][i],methods['pixelperfect'][i]]):
  d.text((col*200+12,row*120+43),str(i),fill='white');canvas.paste(im,(col*200+52,row*120+62),im)
canvas.save(OUT/'six-state-comparison.png')
result=dict(scope='offline diagnostic derivatives only; six states, other15 frames exact',methods=checks,state_metrics=state_metrics,current_sha256=sha(CURRENT),source_sha256=sha(SOURCE),runtime_unchanged=True)
(OUT/'six-state-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(state_metrics)
