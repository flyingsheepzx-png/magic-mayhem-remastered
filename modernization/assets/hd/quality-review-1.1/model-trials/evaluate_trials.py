"""Offline comparable PNGs and diagnostics; does not run the model or game.
Metrics are heuristics, not evidence of semantic or runtime acceptance.
"""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from run_trials import ROOT, SOURCE, OLD, CROP, CONFIG, verify, write_json, LANCZOS
T=(1920,1440)
def rgb(im): return np.asarray(im.convert('RGB'),dtype=np.float32)
def gray(im):
 a=rgb(im); return .299*a[:,:,0]+.587*a[:,:,1]+.114*a[:,:,2]
def font(size=18):
 try: return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)
 except OSError: return ImageFont.load_default()
def contact(name,items,box=None,width=640):
 panels=[]
 for label,im in items:
  panel=im.crop(box) if box else im
  if width and panel.width!=width: panel=panel.resize((width,round(panel.height*width/panel.width)),LANCZOS)
  out=Image.new('RGB',(panel.width,panel.height+36),(24,24,24)); out.paste(panel,(0,36)); ImageDraw.Draw(out).text((8,8),label,font=font(17),fill='white'); panels.append(out)
 cols=3; rows=(len(panels)+cols-1)//cols; pw=max(p.width for p in panels); ph=max(p.height for p in panels)
 out=Image.new('RGB',(pw*cols,ph*rows),(24,24,24))
 for i,p in enumerate(panels): out.paste(p,((i%cols)*pw,(i//cols)*ph))
 out.save(ROOT/name)
def shifted_match(src,test,roi):
 # Source coordinates at 800x600. Search +-12px around each fixed ROI.
 x0,y0,x1,y1=roi; template=src[y0:y1,x0:x1].copy(); template-=template.mean(); tn=np.sqrt(np.sum(template**2)); best=(-2,0,0)
 for dy in range(-12,13):
  for dx in range(-12,13):
   patch=test[y0+dy:y1+dy,x0+dx:x1+dx].copy(); patch-=patch.mean(); norm=np.sqrt(np.sum(patch**2))*tn
   corr=float(np.sum(template*patch)/max(norm,1e-8))
   if corr>best[0]: best=(corr,dx,dy)
 zero=test[y0:y1,x0:x1].copy(); zero-=zero.mean(); z=float(np.sum(template*zero)/max(tn*np.sqrt(np.sum(zero**2)),1e-8))
 return {'best_ncc':round(best[0],4),'best_dx_source_px':best[1],'best_dy_source_px':best[2],'best_displacement_source_px':round(float(np.hypot(best[1],best[2])),2),'zero_shift_ncc':round(z,4),'search_radius_source_px':12,'note':'Correlation displacement is approximate and may reflect changed shading/topology; not landmark verification.'}
def main():
 current=verify(); before=json.loads((ROOT/'input-provenance.json').read_text(encoding='utf-8'))
 assert current['queue_sha256']==before['queue_sha256'],'Shared queue changed; inspect before claiming unchanged'
 source=Image.open(SOURCE).convert('RGB'); base=source.resize(T,LANCZOS)
 items=[('Source pixels (nearest)',source.resize(T,Image.Resampling.NEAREST)),('Lanczos reference',base),('Old Qwen',Image.open(OLD).convert('RGB'))]
 tests={'Lanczos':base,'old-Qwen':items[2][1]}
 for name in CONFIG:
  path=ROOT/(name+'-target.png')
  if not path.exists(): continue
  im=Image.open(path).convert('RGB')
  if CONFIG[name].get('crop'):
   mounted=base.copy(); mounted.paste(im,(round(CROP[0]*2.4),round(CROP[1]*2.4))); mounted.save(ROOT/(name+'-mounted-1920x1440.png')); im=mounted
  items.append((name,im)); tests[name]=im
 contact('comparison-overview.png',items,width=640)
 # Full output resolution crops; labels are the only additions.
 for name,box in {'village-lake':(1032,384,1392,744),'forest':(1248,840,1608,1200),'mountain':(456,24,816,384),'roads':(840,300,1200,660)}.items():
  contact('comparison-'+name+'-1to1.png',items,box,width=None)
 # Protection experiment: only texture residuals inside deliberately small safe regions.
 # No coast, roads, rivers, lake or settlement lies within these masks.
 candidate=tests.get('02-full-readable',tests.get('01-full-conservative'))
 if candidate:
  regions=[(545,330,615,375),(575,390,645,445),(365,145,400,190)]
  mask=Image.new('L',(800,600),0); draw=ImageDraw.Draw(mask)
  for r in regions: draw.ellipse(r,fill=255)
  # Blur then clip to original support: feather inwards; outside protection exact zero.
  soft=mask.filter(ImageFilter.GaussianBlur(4)); m=np.minimum(np.asarray(mask),np.asarray(soft)).astype('uint8'); mask=Image.fromarray(m).resize(T,Image.Resampling.BILINEAR)
  mask.save(ROOT/'protected-texture-mask.png'); alpha=np.asarray(mask,dtype=np.float32)[:,:,None]/255.
  ref_low=rgb(base.filter(ImageFilter.GaussianBlur(5))); gen_low=rgb(candidate.filter(ImageFilter.GaussianBlur(5)))
  gen_hi=rgb(candidate)-gen_low; ref_hi=rgb(base)-ref_low
  # Preserve all original broad shape/shading, bounded +-12 RGB texture change, max blend .45.
  delta=np.clip(gen_hi-ref_hi,-12,12)*alpha*.45
  hybrid=Image.fromarray(np.clip(np.rint(rgb(base)+delta),0,255).astype('uint8')); hybrid.save(ROOT/'04-protected-texture-1920x1440.png')
  outside=np.asarray(mask)==0; maxoutside=int(np.abs(rgb(hybrid)-rgb(base))[outside].max()); maxdelta=int(np.abs(rgb(hybrid)-rgb(base)).max())
  write_json('protected-blend.json',{'model_source_candidate':'02-full-readable' if '02-full-readable' in tests else '01-full-conservative','method':'CPU source-Lanczos anchored high-frequency residual; not ControlNet nor another model','mask_source_ellipses':regions,'gaussian_radius_output_px':5,'residual_clip_rgb':12,'blend':.45,'protected_outside_max_rgb_delta':maxoutside,'global_max_rgb_delta':maxdelta,'changed_fraction':float(np.mean(np.any(rgb(hybrid)!=rgb(base),axis=2))),'limitations':'Preserves excluded coast/roads/rivers/settlements exactly against Lanczos; does not improve them. Allowed interiors may still contain invented forest microstructure.'})
  tests['04-protected-texture']=hybrid
  contact('comparison-protected-forest-1to1.png',[('Lanczos',base),('Full Qwen 02',candidate),('Protected residual',hybrid)],(1248,840,1608,1200),width=None)
 sourceg=gray(source.filter(ImageFilter.GaussianBlur(1.2)))
 landmarks={'mountain':(220,28,310,94),'village':(473,182,532,218),'lake':(412,247,482,291),'road-junction':(382,222,438,261),'east-coast':(654,226,699,289),'south-coast':(570,491,646,544)}
 diagnostics={}
 basea=rgb(base); lowbase=rgb(base.filter(ImageFilter.GaussianBlur(12)))
 for name,im in tests.items():
  a=rgb(im); small=im.resize((800,600),LANCZOS); g=gray(small.filter(ImageFilter.GaussianBlur(1.2))); high=gray(im)-gray(im.filter(ImageFilter.GaussianBlur(1.2)))
  metrics={'mean_abs_rgb_vs_lanczos':round(float(np.mean(np.abs(a-basea))),4),'mean_abs_lowpass_rgb_vs_lanczos':round(float(np.mean(np.abs(rgb(im.filter(ImageFilter.GaussianBlur(12)))-lowbase))),4),'highpass_rms_output_px':round(float(np.sqrt(np.mean(high**2))),4),'landmark_correlation':{key:shifted_match(sourceg,g,roi) for key,roi in landmarks.items()},'scope': 'Only source crop (250,110)-(650,410) changed' if name=='03-context-crop' else 'full image'}
  if name=='03-context-crop':
   box=tuple(round(v*2.4) for v in CROP); x0,y0,x1,y1=box; metrics['crop_mean_abs_rgb_vs_lanczos']=round(float(np.mean(np.abs(a[y0:y1,x0:x1]-basea[y0:y1,x0:x1]))),4)
  diagnostics[name]=metrics
 write_json('offline-metrics.json',{'disclaimer':'Noise/detail energy does not prove useful detail. NCC shift is a heuristic, not semantic acceptance. Candidate03 is an unblended crop mount for diagnosis only. No game launched.','landmark_source_boxes':landmarks,'metrics':diagnostics})
 write_json('postflight-integrity.json',{'source_unchanged':current['source_sha256']==before['source_sha256'],'old_output_unchanged':current['old_sha256']==before['old_sha256'],'queue_bytes_unchanged':current['queue_sha256']==before['queue_sha256'],'source_sha256':current['source_sha256'],'old_sha256':current['old_sha256'],'queue_sha256':current['queue_sha256'],'runtime_test':'not run; pending user testing','writes':'only '+str(ROOT)})
 print(json.dumps({k:{x:v[x] for x in ['mean_abs_rgb_vs_lanczos','mean_abs_lowpass_rgb_vs_lanczos','highpass_rms_output_px']} for k,v in diagnostics.items()},indent=2))
if __name__=='__main__': main()
