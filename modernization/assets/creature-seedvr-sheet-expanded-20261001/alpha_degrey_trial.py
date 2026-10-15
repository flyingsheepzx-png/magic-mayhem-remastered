"""CPU-only de-matting comparison. Source-derived alpha is an estimate, not model alpha."""
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from run_expanded import OUT,write
folder=OUT/'Phoenix/alpha-edge-trial';dest=OUT/'Phoenix/alpha-degrey-trial';dest.mkdir(exist_ok=True)
plan=json.loads((OUT/'manifest.json').read_text());job=next(j for j in plan['jobs'] if j['name']=='Phoenix-PBLD')
labels=['Soft/raw RGB','Previous fringe repair','Unmatte grey','Interior colour extend'];seq={k:[] for k in labels};metrics=[]
for row in job['frames']:
 i=row['ordinal'];raw=Image.open(folder/f'{i:02d}-1.png').convert('RGBA');previous=Image.open(folder/f'{i:02d}-2.png').convert('RGBA');strict=Image.open(folder/f'{i:02d}-0.png').convert('RGBA')
 a=np.array(raw)[:,:,3];rgb=np.array(raw)[:,:,:3].astype(float);binary=np.array(strict)[:,:,3]>0
 fraction=a.astype(float)/255;edge=(a>0)&(a<255)
 # C = alpha*F + (1-alpha)*B; inversion is only approximate for generative SR.
 f=(rgb-(1-fraction[:,:,None])*np.array([48,48,56]))/np.maximum(fraction[:,:,None],.20)
 un=rgb.copy();un[edge]=np.clip(f[edge],0,255)
 # Conservative donor set: 1 output pixel inside opaque source; nearby donors only.
 support=Image.fromarray((binary*255).astype('uint8'));core=(np.array(support.filter(ImageFilter.MinFilter(3)))>0)&(a>=240)
 yy,xx=np.where(core);extended=rgb.copy();changed=0;fallback=0
 for y,x in zip(*np.where(edge)):
  near=(np.abs(yy-y)<=4)&(np.abs(xx-x)<=4)
  if not near.any():fallback+=1;continue
  ys=yy[near];xs=xx[near];distance=(ys-y)**2+(xs-x)**2;best=distance.min();chosen=distance==best
  extended[y,x]=rgb[ys[chosen],xs[chosen]].mean(0);changed+=1
 for label,array in [('Unmatte grey',un),('Interior colour extend',extended)]:
  im=Image.fromarray(np.rint(array).clip(0,255).astype('uint8')).convert('RGBA');im.putalpha(raw.getchannel('A'));im.save(dest/f'{i:02d}-{label.replace(" ","-")}.png');seq[label].append(im)
 seq[labels[0]].append(raw);seq[labels[1]].append(previous)
 metrics.append({'frame':row['name'],'partial_pixels':int(edge.sum()),'unmatte_out_of_range_pixels':int((edge&((f<0).any(2)|(f>255).any(2))).sum()),'interior_extended_pixels':changed,'no_nearby_core_donor_pixels':fallback,'alpha_unchanged':True})
for bgname,bg in [('grey',(48,48,56)),('black','black'),('white','white')]:
 anim=[]
 # common original-offset crop, with padding, prevents frame recentering.
 boxes=[]
 for row in job['frames']:
  x,y=[v*2 for v in row['local_position']];im=seq[labels[0]][row['ordinal']];boxes.append((x,y,x+im.width,y+im.height))
 box=(min(b[0] for b in boxes)-4,min(b[1] for b in boxes)-4,max(b[2] for b in boxes)+4,max(b[3] for b in boxes)+4)
 zoom=3;w=(box[2]-box[0])*zoom;h=(box[3]-box[1])*zoom
 for i,row in enumerate(job['frames']):
  c=Image.new('RGB',(w*4,h+45),bg);d=ImageDraw.Draw(c)
  for k,label in enumerate(labels):
   base=Image.new('RGBA',tuple(v*2 for v in job['cell_size']));base.paste(seq[label][i],tuple(v*2 for v in row['local_position']));base=base.crop(box)
   composite=Image.new('RGB',base.size,bg);composite.paste(base,(0,0),base);c.paste(composite.resize((w,h),Image.Resampling.NEAREST),(k*w,45));d.text((k*w+7,7),label,fill='#ff00ff');d.text((k*w+7,24),row['name']+' | display 3x',fill='#ff00ff')
  anim.append(c);c.save(dest/f'frame-{i:02d}-{bgname}.png')
 anim[0].save(dest/f'animation-{bgname}.png',save_all=True,append_images=anim[1:],duration=125,loop=0)
 anim[0].save(dest/f'animation-{bgname}.gif',save_all=True,append_images=anim[1:],duration=125,loop=0)
write(dest/'validation.json',{'background_used_in_inference':[48,48,56],'no_new_inference':True,'methods':labels,'frames':metrics,'limitations':'Alpha is derived from source, not inferred by model. Matte inversion assumes linear RGB compositing though SR is nonlinear and sRGB. Donor extension can blur small colour details; no donor beyond four output pixels. Neither method reconstructs missing anatomy.'})
(dest/'index.html').write_text('<meta charset="utf-8"><style>body{background:#222;color:white}img{max-width:none}.scroll{overflow:auto}</style><h1>Phoenix grey-edge cleanup</h1>'+''.join(f'<h2>{b}</h2><div class="scroll"><img src="animation-{b}.png"></div>' for b in ['white','black','grey']),encoding='utf-8')
print(json.dumps(metrics,indent=2))
