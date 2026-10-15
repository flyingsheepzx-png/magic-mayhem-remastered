"""CPU-only comparison of the same source frames in two SeedVR2 atlas layouts."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'modernization/assets/creature-sequence-review-20260930'
NEW=ROOT/'modernization/assets/creature-seedvr-sheet-expanded-20261001'
OUT=ROOT/'modernization/logs/creature-sheet-packing-20261001'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 old=json.loads((OLD/'manifest.json').read_text())
 new=json.loads((NEW/'manifest.json').read_text())
 job=next(j for j in new['jobs'] if j['name']=='Bat-AALF')
 assert job['status']=='complete'
 assert sha(Path(job['output']))==job['output_sha256']
 assert job['source_sha256']==old['source_sha256']
 oldjob=next(j for j in old['jobs'] if j['name']=='seedvr-sheet')
 assert sha(Path(oldjob['output']))==oldjob['output_sha256']
 raw=Image.open(job['output']).convert('RGB')
 OUT.mkdir(exist_ok=True)
 picture=Image.new('RGB',(6*240,4*250),(48,48,56));draw=ImageDraw.Draw(picture)
 labels=['Source nearest 2x','Lanczos 2x','SeedVR old six-frame sheet','SeedVR new eight-frame sheet']
 rows=[]
 for k,previous in enumerate(old['frames']):
  current=next(f for f in job['frames'] if f['name']==previous['name'])
  assert all(current[field]==previous[field] for field in ['index','width','height','offset','flags'])
  src=Image.open(current['source_png']).convert('RGBA')
  assert sha(Path(current['source_png']))==previous['source_png_sha256']
  size=(src.width*2,src.height*2)
  alpha=src.getchannel('A').resize(size,Image.Resampling.NEAREST)
  x,y=[(a+b)*2 for a,b in zip(current['cell_origin'],current['local_position'])]
  updated=raw.crop((x,y,x+size[0],y+size[1])).convert('RGBA');updated.putalpha(alpha)
  previous_image=Image.open(OLD/'seedvr-sheet'/f'frame-{k:02d}-2x.png').convert('RGBA')
  assert previous_image.size==size
  assert np.array_equal(np.array(previous_image.getchannel('A')),np.array(alpha))
  mask=np.array(alpha)>0
  difference=np.abs(np.array(updated.convert('RGB'),dtype=float)-np.array(previous_image.convert('RGB'),dtype=float))
  low=[np.array(im.convert('RGB').filter(ImageFilter.GaussianBlur(3)),dtype=float) for im in [updated,previous_image]]
  rows.append({'frame':current['name'],'index':current['index'],'shared_source_exact':True,'rgb_layout_sensitivity_mae':float(difference[mask].mean()),'low_frequency_layout_sensitivity_mae':float(np.abs(low[0]-low[1])[mask].mean())})
  nearest=src.resize(size,Image.Resampling.NEAREST)
  lanczos=src.resize(size,Image.Resampling.LANCZOS);lanczos.putalpha(alpha)
  for r,im in enumerate([nearest,lanczos,previous_image,updated]):
   draw.text((k*240+8,r*250+8),labels[r],fill='white')
   draw.text((k*240+8,r*250+25),current['name'],fill='white')
   picture.paste(im,(k*240+(240-im.width)//2,r*250+65),im)
 picture.save(OUT/'comparison.png')
 report={'scope':'Same six source frames, fixed default SeedVR seed; old 3x2 / 128px cells vs new 4x2 / 160x128px cells. Source hashes, metadata and alpha verified.', 'limits':'Layout, context and output dimensions change together. No repeated-run control; this is pipeline sensitivity, not isolated causal proof or gameplay acceptance.', 'rows':rows,'average_rgb_layout_sensitivity_mae':sum(r['rgb_layout_sensitivity_mae'] for r in rows)/len(rows)}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
