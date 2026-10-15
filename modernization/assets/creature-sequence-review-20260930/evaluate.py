"""CPU-only derivative validation, motion-relative error, sheets and APNG previews."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
OUT=Path(__file__).resolve().parent
plan=json.loads((OUT/'manifest.json').read_text())
FF='E:/AI/LosslessCut/resources/ffmpeg.exe'
variants={};metrics={}
rows=plan['frames']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def align(images,scale):
 result=[]
 for im,row in zip(images,rows):
  c=Image.new('RGBA',(128*scale,128*scale));c.paste(im,tuple(v*scale for v in row['position']));result.append(c)
 return result
source=[Image.open(OUT/'sources'/f'{i:02d}.png').convert('RGBA') for i in range(6)]
base=[]
for im in source:
 b=im.resize((im.width*2,im.height*2),Image.Resampling.LANCZOS);b.putalpha(im.getchannel('A').resize(b.size,Image.Resampling.NEAREST));base.append(b)
variants['lanczos']=align(base,2)
for job in plan['jobs']:
 if job['status']!='complete':continue
 dest=OUT/job['name'];p=Path(job['output']);assert sha(p)==job['output_sha256']
 frames=[]
 if job['mode']=='video':
  decoded=dest/'decoded';decoded.mkdir(exist_ok=True)
  subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-i',str(p),'-vsync','0',str(decoded/'%02d.png')],check=True,creationflags=0x08000000)
  video=list(sorted(decoded.glob('*.png')));assert len(video)==6,(job['name'],len(video))
 else:
  sheet=Image.open(p).convert('RGB')
  if job['mode']=='qwen':sheet=sheet.crop((0,170,1024,853))
  sheet=sheet.resize((768,512),Image.Resampling.LANCZOS)
 validations=[]
 for i,(im,row) in enumerate(zip(source,rows)):
  if job['mode']=='video':canvas=Image.open(video[i]).convert('RGB').resize((256,256),Image.Resampling.LANCZOS)
  else:canvas=sheet.crop(((i%3)*256,(i//3)*256,(i%3+1)*256,(i//3+1)*256))
  x,y=[v*2 for v in row['position']];w,h=im.width*2,im.height*2
  enhanced=canvas.crop((x,y,x+w,y+h)).convert('RGBA');alpha=im.getchannel('A').resize((w,h),Image.Resampling.NEAREST);enhanced.putalpha(alpha)
  enhanced.save(dest/f'frame-{i:02d}-2x.png')
  native=enhanced.resize(im.size,Image.Resampling.LANCZOS);native.putalpha(im.getchannel('A'));native.save(dest/f'frame-{i:02d}-native.png')
  assert native.size==im.size and np.array_equal(np.array(native)[:,:,3],np.array(im)[:,:,3])
  assert np.array_equal(np.array(enhanced)[:,:,3],np.array(alpha))
  frames.append(enhanced)
  validations.append({'index':row['index'],'name':row['name'],'dimensions':im.size,'offset':row['offset'],'flags':row['flags'],'native_dimensions_exact':True,'native_alpha_exact':True,'2x_alpha_nearest_exact':True,'native_sha256':sha(dest/f'frame-{i:02d}-native.png')})
 variants[job['name']]=align(frames,2)
 (dest/'frame-validation.json').write_text(json.dumps(validations,indent=2)+'\n')
base_arr=np.stack([np.array(im)[:,:,:3].astype(float) for im in variants['lanczos']]);mask=np.stack([np.array(im)[:,:,3]>0 for im in variants['lanczos']])
for name,ims in variants.items():
 dest=OUT/name;dest.mkdir(exist_ok=True)
 arr=np.stack([np.array(im)[:,:,:3].astype(float) for im in ims]);residual=arr-base_arr
 intersection=mask[1:]&mask[:-1]
 # Motion-relative difference: changes in model residual, on shared opaque pixels.
 # This is a proxy, not optical-flow correspondence or a pure flicker measurement.
 temporal=float(np.abs(np.diff(residual,axis=0))[intersection].mean())
 rgb=float(np.abs(residual)[mask].mean())
 low=np.stack([np.array(im.convert('RGB').filter(ImageFilter.GaussianBlur(3))).astype(float) for im in ims])
 lowbase=np.stack([np.array(im.convert('RGB').filter(ImageFilter.GaussianBlur(3))).astype(float) for im in variants['lanczos']])
 metrics[name]={'rgb_drift_mae':round(rgb,4),'motion_relative_residual_delta_mae':round(temporal,4),'low_frequency_structure_drift_mae':round(float(np.abs(low-lowbase)[mask].mean()),4)}
 # Background-composited APNG preserves full RGBA and no GIF palette loss.
 preview=[]
 for im in ims:
  c=Image.new('RGBA',im.size,(48,48,56,255));c.alpha_composite(im);preview.append(c)
 preview[0].save(dest/'animation.png',save_all=True,append_images=preview[1:],duration=125,loop=0,disposal=0,blend=0)
 preview[0].convert('RGB').save(dest/'animation.gif',save_all=True,append_images=[im.convert('RGB') for im in preview[1:]],duration=125,loop=0)
sheet=Image.new('RGB',(6*256+180,len(variants)*280),(30,30,36));d=ImageDraw.Draw(sheet)
for y,(name,ims) in enumerate(variants.items()):
 d.text((8,y*280+12),name[:24],fill='white')
 for i,im in enumerate(ims):
  bg=Image.new('RGB',im.size,(48,48,56));bg.paste(im,(0,0),im);sheet.paste(bg,(180+i*256,y*280+24));d.text((180+i*256,y*280+6),rows[i]['name'],fill='white')
sheet.save(OUT/'comparison.png')
combined=[]
for i in range(6):
 c=Image.new('RGB',(3*300,3*290),(30,30,36));draw=ImageDraw.Draw(c)
 for k,(name,ims) in enumerate(variants.items()):
  x=(k%3)*300;y=(k//3)*290;draw.text((x+8,y+8),name[:34],fill='white')
  im=ims[i];bg=Image.new('RGB',im.size,(48,48,56));bg.paste(im,(0,0),im);c.paste(bg,(x+22,y+26))
 combined.append(c)
combined[0].save(OUT/'comparison-animation.gif',save_all=True,append_images=combined[1:],duration=125,loop=0)
combined[0].save(OUT/'comparison-animation.png',save_all=True,append_images=combined[1:],duration=125,loop=0)
assert sha(Path(plan['source']))==plan['source_sha256']
assert sha(Path(plan['source']).with_name('bat.ani'))==plan['ani_sha256']
report={'scope':plan['scope'],'metrics':metrics,'failed':[{'name':j['name'],'error':j.get('error')} for j in plan['jobs'] if j['status']=='failed'],'source_still_exact':True,'native_alpha_dimensions_offsets_flags_preserved':True,'metric_limits':'No optical flow; residual delta includes legitimate texture motion. Alpha locking guarantees silhouette only, not internal anatomy. Six frame fixed 125ms preview is not verified ANI timing. Video results include Manager encoding artifacts. Sheet runs have no temporal context.'}
(OUT/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
