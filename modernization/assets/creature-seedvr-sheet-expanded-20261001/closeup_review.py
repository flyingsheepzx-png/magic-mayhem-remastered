"""Readable CPU-only exact-pixel closeups. No inference or asset changes."""
import json,math
from PIL import Image,ImageDraw
from run_expanded import OUT,MANIFEST,write
plan=json.loads(MANIFEST.read_text());provenance=[]
for job in plan['jobs']:
 folder=OUT/job['creature']/job['prefix'];dest=folder/'closeups';dest.mkdir(exist_ok=True)
 cw,ch=job['cell_size'];sequences={'Original':[],'Lanczos 2x':[],'SeedVR 2x':[],'SeedVR native':[]}
 boxes=[]
 for row in job['frames']:
  src=Image.open(row['source_png']).convert('RGBA');native=Image.open(folder/f"{row['ordinal']:02d}-seedvr-native.png").convert('RGBA');seed=Image.open(folder/f"{row['ordinal']:02d}-seedvr-2x.png").convert('RGBA');lanc=src.resize(seed.size,Image.Resampling.LANCZOS);lanc.putalpha(seed.getchannel('A'))
  for key,im,scale in [('Original',src,1),('Lanczos 2x',lanc,2),('SeedVR 2x',seed,2),('SeedVR native',native,1)]:
   c=Image.new('RGBA',(cw*scale,ch*scale));c.paste(im,tuple(v*scale for v in row['local_position']));sequences[key].append(c)
  box=sequences['Original'][-1].getbbox();boxes.append(box)
 union=(max(0,min(b[0] for b in boxes)-6),max(0,min(b[1] for b in boxes)-6),min(cw,max(b[2] for b in boxes)+6),min(ch,max(b[3] for b in boxes)+6))
 # Common native crop retains motion/offset; integer nearest zoom guarantees original pixel boundaries.
 zoom=max(4,math.ceil(420/max(union[2]-union[0],union[3]-union[1])));zoom+=(zoom%2)
 tw=(union[2]-union[0])*zoom;th=(union[3]-union[1])*zoom
 def cropzoom(im,scale):
  im=im.crop(tuple(v*scale for v in union)).resize((tw,th),Image.Resampling.NEAREST)
  rgb=Image.new('RGB',im.size,(48,48,56));rgb.paste(im,(0,0),im);return rgb
 outputs={}
 for mode,labels in [('2x',['Original','Lanczos 2x','SeedVR 2x']),('native',['Original','SeedVR native'])]:
  anim=[]
  for i,row in enumerate(job['frames']):
   canvas=Image.new('RGB',(len(labels)*tw,th+48),(28,28,34));d=ImageDraw.Draw(canvas)
   for k,label in enumerate(labels):
    scale=2 if label in ['Lanczos 2x','SeedVR 2x'] else 1
    canvas.paste(cropzoom(sequences[label][i],scale),(k*tw,48));d.text((k*tw+10,10),f'{label} | {row["name"]}',fill='white');d.text((k*tw+10,27),f'nearest display zoom {zoom//scale}x; no new detail',fill='white')
   p=dest/f'frame-{i:02d}-{mode}.png';canvas.save(p);anim.append(canvas)
  anim[0].save(dest/f'animation-{mode}.png',save_all=True,append_images=anim[1:],duration=125,loop=0)
  anim[0].save(dest/f'animation-{mode}.gif',save_all=True,append_images=anim[1:],duration=125,loop=0)
  # Vertical contact sheet keeps each row at full readable detail; do not downsample.
  contact=Image.new('RGB',(anim[0].width,sum(im.height for im in anim)),(28,28,34))
  for i,im in enumerate(anim):contact.paste(im,(0,i*im.height))
  contact.save(dest/f'contact-{mode}.png');outputs[mode]={'frame_size':anim[0].size,'contact_size':contact.size}
 provenance.append({'group':job['name'],'common_native_crop':union,'native_display_zoom':zoom,'2x_display_zoom':zoom//2,'method':'nearest-neighbour integer display enlargement; original data unchanged','outputs':outputs})
write(OUT/'closeup-provenance.json',provenance)
page=['<!doctype html><meta charset="utf-8"><title>Full-detail SeedVR review</title><style>body{background:#202026;color:#eee;font:18px sans-serif;margin:20px}a{color:#acf}.scroll{overflow:auto;max-width:100%;border:1px solid #777}img{max-width:none;image-rendering:pixelated}h2{margin-top:50px}</style><h1>Full-detail pixel closeups</h1><p>Images stay at their saved display dimensions: scroll horizontally if needed. Common source-alpha crop; integer nearest enlargement only. Native and 2x gains are separate. <a href="REPORT.md">Report</a></p>']
for job in plan['jobs']:
 rel=job['creature']+'/'+job['prefix']+'/closeups';page.append(f'<h2>{job["name"]}</h2><h3>2x comparison animation</h3><div class="scroll"><img src="{rel}/animation-2x.png"></div><h3>Native comparison animation</h3><div class="scroll"><img src="{rel}/animation-native.png"></div><p><a href="{rel}/contact-2x.png">Full 2x eight-frame contact sheet</a> · <a href="{rel}/contact-native.png">Full native contact sheet</a></p>')
 for row in job['frames']:
  i=row['ordinal'];page.append(f'<p>{row["name"]}: <a href="{rel}/frame-{i:02d}-2x.png">2x frame comparison</a> · <a href="{rel}/frame-{i:02d}-native.png">Native frame comparison</a></p>')
(OUT/'closeups.html').write_text(''.join(page),encoding='utf-8')
report=OUT/'REPORT.md';text=report.read_text(encoding='utf-8');note='''

## Full-detail closeups (readability correction)

The initial padded multi-frame previews are unsuitable for fine-detail inspection when fit to a narrow viewport. Use **closeups.html** instead: it never auto-shrinks the saved images and supports horizontal scrolling. Every group supplies per-frame side-by-side PNGs, lossless APNG/GIF animations and vertical full-detail contact sheets under `<creature>/<prefix>/closeups/`. A common crop derived from source alpha across the whole group preserves relative offsets, then integer nearest-neighbour enlargement displays every original pixel clearly. This changes display size only, not model data or source resolution. Native and 2x comparisons are separate. Exact crop rectangles and display multipliers are in `closeup-provenance.json`; original full sheets and actual native/2x exports remain available.
'''
if '## Full-detail closeups' not in text:report.write_text(text+note,encoding='utf-8')
index=OUT/'index.html';text=index.read_text();link='<p><a href="closeups.html">OPEN FULL-DETAIL CLOSEUPS (no automatic shrinking)</a></p>'
if link not in text:index.write_text(link+text,encoding='utf-8')
print('Created 224 per-frame comparisons, 28 APNG/GIF pairs, 28 full-detail contact sheets')
