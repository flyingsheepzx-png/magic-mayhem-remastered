"""CPU-only Phoenix alpha edge experiment, reusing saved SeedVR RGB."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from run_expanded import OUT,sha,write
plan=json.loads((OUT/'manifest.json').read_text());job=next(j for j in plan['jobs'] if j['name']=='Phoenix-PBLD')
folder=OUT/'Phoenix/PBLD';dest=OUT/'Phoenix/alpha-edge-trial';dest.mkdir(exist_ok=True)
raw=Image.open(job['output']).convert('RGB');assert sha(job['output'])==job['output_sha256']
labels=['Strict binary','Soft alpha / raw RGB','Soft alpha / edge RGB repair'];seq={k:[] for k in labels};records=[]
for row in job['frames']:
 src=Image.open(row['source_png']).convert('RGBA');w,h=src.size
 binary=src.getchannel('A').resize((w*2,h*2),Image.Resampling.NEAREST)
 # 1px input padding preserves antialias at the crop boundary.
 pad=Image.new('L',(w+2,h+2));pad.paste(src.getchannel('A'),(1,1))
 soft=pad.resize(((w+2)*2,(h+2)*2),Image.Resampling.LANCZOS).crop((2,2,w*2+2,h*2+2))
 x=2*(row['cell_origin'][0]+row['local_position'][0]);y=2*(row['cell_origin'][1]+row['local_position'][1]);rgb=raw.crop((x,y,x+w*2,y+h*2))
 # Limit new coverage to 2 output pixels from exact opaque support, excluding ringing far away.
 a=np.array(soft);b=np.array(binary);near=np.array(binary.filter(ImageFilter.MaxFilter(5)))>0;a[~near]=0;soft=Image.fromarray(a)
 pixels=np.array(rgb).copy();opaque=b>0;fringe=(a>0)&~opaque
 # Copy nearest covered RGB into newly exposed fringe, avoiding grey sheet-background halos.
 ys,xs=np.where(opaque)
 for yy,xx in zip(*np.where(fringe)):
  distance=(ys-yy)**2+(xs-xx)**2;k=int(distance.argmin());pixels[yy,xx]=pixels[ys[k],xs[k]]
 for label,color,alpha in [(labels[0],rgb,binary),(labels[1],rgb,soft),(labels[2],Image.fromarray(pixels),soft)]:
  im=color.convert('RGBA');im.putalpha(alpha);im.save(dest/f"{row['ordinal']:02d}-{labels.index(label)}.png")
  seq[label].append(im)
 records.append({'name':row['name'],'size':[w*2,h*2],'strict_alpha_values':np.unique(b).tolist(),'soft_partial_pixels':int(((a>0)&(a<255)).sum()),'new_fringe_pixels':int(fringe.sum()),'original_opaque_pixels_became_partial':int((opaque&(a<255)).sum()),'soft_alpha_min_max':[int(a.min()),int(a.max())]})
def panel(i):
 ims=[seq[k][i] for k in labels];w,h=ims[0].size;zoom=3
 c=Image.new('RGB',(w*zoom*3,h*zoom*3+96),(24,24,30));d=ImageDraw.Draw(c)
 for col,(label,im) in enumerate(zip(labels,ims)):
  d.text((col*w*zoom+8,8),label,fill='white')
  for r,bg in enumerate(['#303038','black','white']):
   out=Image.new('RGB',im.size,bg);out.paste(im,(0,0),im);out=out.resize((w*zoom,h*zoom),Image.Resampling.NEAREST);c.paste(out,(col*w*zoom,32+r*(h*zoom+24)));d.text((col*w*zoom+5,32+r*(h*zoom+24)),bg,fill='#ff00ff')
 return c
panel(0).save(dest/'comparison.png')
# Individual backgrounds / all frames with constant aligned geometry, no camera recentering.
for bgname,bg in [('grey','#303038'),('black','black'),('white','white')]:
 previews=[]
 for i,row in enumerate(job['frames']):
  cw,ch=job['cell_size'];zoom=2;c=Image.new('RGB',(cw*2*zoom*3,ch*2*zoom+30),bg);d=ImageDraw.Draw(c)
  for col,label in enumerate(labels):
   base=Image.new('RGBA',(cw*2,ch*2));base.paste(seq[label][i],tuple(v*2 for v in row['local_position']));out=Image.new('RGB',base.size,bg);out.paste(base,(0,0),base);c.paste(out.resize((cw*2*zoom,ch*2*zoom),Image.Resampling.NEAREST),(col*cw*2*zoom,30));d.text((col*cw*2*zoom+8,8),label,fill='#ff00ff')
  previews.append(c)
 previews[0].save(dest/f'animation-{bgname}.png',save_all=True,append_images=previews[1:],duration=125,loop=0)
 previews[0].save(dest/f'animation-{bgname}.gif',save_all=True,append_images=previews[1:],duration=125,loop=0)
write(dest/'validation.json',{'method':'source-derived Lanczos alpha at 2x, max 2px outside binary support; no GPU, no runtime edits','raw_model_sha256':job['output_sha256'],'records':records,'limits':'Not alpha predicted by SeedVR; coverage softened from source mask. Nearest opaque fringe RGB is a heuristic. Engine SPR alpha support not changed or verified.'})
(dest/'REPORT.md').write_text('''# Phoenix soft-edge alpha trial

CPU-only eight-frame PBLD experiment reuses the saved SeedVR2 sheet RGB. No new inference or runtime changes.

Three arms: strict binary source alpha; Lanczos antialiased source alpha using unchanged raw RGB; identical antialiased alpha with newly exposed fringe RGB copied from the nearest originally covered pixel. Output dimensions are exactly 2x the source. New alpha support is restricted to two output pixels around original coverage. Padding prevents crop-edge resampling artefacts; no frame dimensions/offsets are changed.

Partial alpha smooths diagonal outlines at display size, but does not create more anatomical detail or establish higher accuracy. Raw RGB on the newly exposed fringe includes the grey inference-sheet background and can cause grey halos on white/black. Fringe repair mitigates this contamination heuristically; thin feathers and changing edge colours still require review. Antialiased alpha also changes some formerly opaque edge pixels to partial coverage.

Use comparison.png (first frame, grey/black/white backgrounds) and lossless animation-grey/black/white.png for eight frames. GIF is palette-quantized and should not be used to judge alpha. validation.json records new coverage and partial alpha counts. Saved numbered RGBA PNGs preserve actual alpha.

This demonstrates image-domain antialiasing only. Native SPR uses transparent skips/opaque runs; preserving these partial alpha values in-game requires separately verifying or changing renderer/asset support. No claim of runtime compatibility is made.
''',encoding='utf-8')
print(records)
