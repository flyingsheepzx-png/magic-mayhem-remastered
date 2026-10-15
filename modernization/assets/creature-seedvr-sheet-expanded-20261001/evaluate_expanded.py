"""CPU-only validation/metrics/contact sheets/native and 2x animation review."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from run_expanded import OUT,MANIFEST,sha,write,verify_sources,audit_selectors
plan=json.loads(MANIFEST.read_text());verify_sources(plan);audit_selectors(plan)
def metric(ims,base):
 a=np.stack([np.array(im)[:,:,:3].astype(float) for im in ims]);b=np.stack([np.array(im)[:,:,:3].astype(float) for im in base]);m=np.stack([np.array(im)[:,:,3]>0 for im in base]);r=a-b;over=m[1:]&m[:-1]
 low=lambda seq:np.stack([np.array(im.convert('RGB').filter(ImageFilter.GaussianBlur(3))).astype(float) for im in seq])
 return {'rgb_drift_mae':float(np.abs(r)[m].mean()),'motion_relative_residual_delta_mae':float(np.abs(np.diff(r,axis=0))[over].mean()),'low_frequency_structure_drift_mae':float(np.abs(low(ims)-low(base))[m].mean())}
def canvas(im,row,size,scale):
 c=Image.new('RGBA',(size[0]*scale,size[1]*scale));c.paste(im,tuple(v*scale for v in row['local_position']));return c
def show(im,bg):
 c=Image.new('RGB',im.size,bg);c.paste(im,(0,0),im);return c
def animate(path,ims):
 frames=[show(im,(48,48,56)) for im in ims]
 frames[0].save(path.with_suffix('.png'),save_all=True,append_images=frames[1:],duration=125,loop=0)
 frames[0].save(path.with_suffix('.gif'),save_all=True,append_images=frames[1:],duration=125,loop=0)
results=[];collections={}
for job in plan['jobs']:
 if job['status']!='complete':continue
 dest=Path(job['input']).parent;assert sha(job['output'])==job['output_sha256'];raw=Image.open(job['output']).convert('RGB');assert list(raw.size)==job['target_size']
 original=[];base=[];seed=[];native=[];diagnostics=[]
 for row in job['frames']:
  p=Path(row['source_png']);assert sha(p)==row['source_png_sha256'];src=Image.open(p).convert('RGBA');w,h=src.size
  alpha=src.getchannel('A').resize((w*2,h*2),Image.Resampling.NEAREST)
  ox,oy=[v*2 for v in row['cell_origin']];cw,ch=[v*2 for v in job['cell_size']];cell=raw.crop((ox,oy,ox+cw,oy+ch))
  x,y=[v*2 for v in row['local_position']];crop=cell.crop((x,y,x+w*2,y+h*2));crop.save(dest/f"{row['ordinal']:02d}-prealpha.png")
  enhanced=crop.convert('RGBA');enhanced.putalpha(alpha);enhanced.save(dest/f"{row['ordinal']:02d}-seedvr-2x.png")
  small=enhanced.resize((w,h),Image.Resampling.LANCZOS);small.putalpha(src.getchannel('A'));small.save(dest/f"{row['ordinal']:02d}-seedvr-native.png")
  lanc=src.resize((w*2,h*2),Image.Resampling.LANCZOS);lanc.putalpha(alpha)
  assert small.size==src.size and np.array_equal(np.array(small)[:,:,3],np.array(src)[:,:,3]);assert np.array_equal(np.array(enhanced)[:,:,3],np.array(alpha))
  maskim=Image.new('L',cell.size);maskim.paste(alpha,(x,y));mask=np.array(maskim)>0
  dilation=np.array(maskim.filter(ImageFilter.MaxFilter(9)))>0;erosion=np.array(maskim.filter(ImageFilter.MinFilter(5)))>0
  near=dilation&~mask;far=~dilation;inner=mask&~erosion
  pixels=np.array(cell).astype(float);dev=np.abs(pixels-np.array([48,48,56])).max(2)
  # Threshold >24 above constant submitted RGB background; not a semantic segmentation mask.
  external=(dev>24)&~mask
  border=np.zeros_like(mask);border[:16,:]=True;border[-16:,:]=True;border[:,:16]=True;border[:,-16:]=True
  basecell=canvas(lanc,row,job['cell_size'],2);b=np.array(basecell)[:,:,:3].astype(float)
  thin=mask&~(np.array(maskim.filter(ImageFilter.MinFilter(9)))>0)
  edge_mae=float(np.abs(pixels-b)[inner].mean());thin_mae=float(np.abs(pixels-b)[thin].mean())
  diagnostic=show(basecell,(48,48,56));a=np.array(diagnostic);a[external]=[255,0,255];Image.fromarray(a).save(dest/f"{row['ordinal']:02d}-contamination.png")
  diagnostics.append({'index':row['index'],'name':row['name'],'palette_selector':row['palette_selector'],'mask_offset_32':row['mask_offset_32'],'mask_offset_36':row['mask_offset_36'],'native_size_exact':True,'native_alpha_exact':True,'2x_alpha_exact':True,'offset_flags_index_preserved':True,'prealpha_external_pixels_gt24':int(external.sum()),'near_edge_halo_pixels_gt24':int(((dev>24)&near).sum()),'far_background_pixels_gt24':int(((dev>24)&far).sum()),'cell_border_pixels_gt24':int(((dev>24)&border).sum()),'prealpha_external_fraction_of_source_opaque':float(external.sum()/max(1,mask.sum())),'inner_edge_rgb_mae':edge_mae,'thin_feature_rgb_mae':thin_mae,'native_output_sha256':sha(dest/f"{row['ordinal']:02d}-seedvr-native.png"),'2x_output_sha256':sha(dest/f"{row['ordinal']:02d}-seedvr-2x.png")})
  original.append(canvas(src,row,job['cell_size'],1));base.append(basecell);seed.append(canvas(enhanced,row,job['cell_size'],2));native.append(canvas(small,row,job['cell_size'],1))
 write(dest/'frame-validation.json',diagnostics)
 rowresult={'name':job['name'],'creature':job['creature'],'prefix':job['prefix'],'frames':len(seed),'job_id':job['job_id'],'metrics_2x':metric(seed,base),'metrics_native':metric(native,original),'diagnostics':{'external_fraction_mean':float(np.mean([r['prealpha_external_fraction_of_source_opaque'] for r in diagnostics])),'halo_pixels_total':sum(r['near_edge_halo_pixels_gt24'] for r in diagnostics),'far_pixels_total':sum(r['far_background_pixels_gt24'] for r in diagnostics),'border_pixels_total':sum(r['cell_border_pixels_gt24'] for r in diagnostics),'inner_edge_mae_mean':float(np.mean([r['inner_edge_rgb_mae'] for r in diagnostics])),'thin_feature_mae_mean':float(np.mean([r['thin_feature_rgb_mae'] for r in diagnostics]))}}
 results.append(rowresult)
 for label,ims in [('original-native',original),('lanczos-2x',base),('seedvr-2x',seed),('seedvr-native',native)]:animate(dest/('animation-'+label),ims)
 collections.setdefault(job['creature'],[]).append((job,original,base,seed,native))
for creature,groups in collections.items():
 out=OUT/creature;cw,ch=groups[0][0]['cell_size'];width=8*cw*2+170
 sheet=Image.new('RGB',(width,len(groups)*3*(ch*2+30)),(25,25,30));d=ImageDraw.Draw(sheet)
 native_sheet=Image.new('RGB',(8*cw+170,len(groups)*2*(ch+30)),(25,25,30));nd=ImageDraw.Draw(native_sheet)
 for g,(job,orig,base,seed,native) in enumerate(groups):
  for r,(label,ims) in enumerate([('original nearest 2x',[im.resize((cw*2,ch*2),Image.Resampling.NEAREST) for im in orig]),('Lanczos 2x',base),('SeedVR2 2x',seed)]):
   y=(g*3+r)*(ch*2+30);d.text((8,y+12),job['prefix']+' '+label,fill='white')
   for i,im in enumerate(ims):sheet.paste(show(im,(48,48,56)),(170+i*cw*2,y+26));d.text((170+i*cw*2,y+6),job['frames'][i]['name'],fill='white')
  for r,(label,ims) in enumerate([('original native',orig),('SeedVR native',native)]):
   y=(g*2+r)*(ch+30);nd.text((8,y+12),job['prefix']+' '+label,fill='white')
   for i,im in enumerate(ims):native_sheet.paste(show(im,(48,48,56)),(170+i*cw,y+26))
 sheet.save(out/'comparison-2x.png');native_sheet.save(out/'comparison-native.png')
 sheet.resize((min(1600,sheet.width),round(sheet.height*min(1600,sheet.width)/sheet.width)),Image.Resampling.LANCZOS).save(out/'comparison-preview.png')
 # Paired prefix grids, same-origin native and 2x animated comparisons.
 for scale in [1,2]:
  previews=[]
  for i in range(8):
   labels=['Original nearest 2x','Lanczos 2x','SeedVR2 2x'] if scale==2 else ['Original native','SeedVR native']
   c=Image.new('RGB',(len(labels)*cw*scale,len(groups)*(ch*scale+30)),(48,48,56));draw=ImageDraw.Draw(c)
   for g,(job,orig,base,seed,native) in enumerate(groups):
    ims=[orig[i].resize((cw*2,ch*2),Image.Resampling.NEAREST),base[i],seed[i]] if scale==2 else [orig[i],native[i]]
    for k,(label,im) in enumerate(zip(labels,ims)):
     draw.text((k*cw*scale+4,g*(ch*scale+30)+4),job['prefix']+' '+label,fill='white');c.paste(show(im,(48,48,56)),(k*cw*scale,g*(ch*scale+30)+26))
   previews.append(c)
  previews[0].save(out/f'comparison-animation-{scale}x.png',save_all=True,append_images=previews[1:],duration=125,loop=0)
  previews[0].save(out/f'comparison-animation-{scale}x.gif',save_all=True,append_images=previews[1:],duration=125,loop=0)
 # Edge/colour check on black and white for first/most-drift frame per group.
 checks=Image.new('RGB',(4*cw*2,len(groups)*ch*2),(80,80,80))
 for g,(job,orig,base,seed,native) in enumerate(groups):
  for k,(im,bg) in enumerate([(base[0],'black'),(seed[0],'black'),(base[0],'white'),(seed[0],'white')]):checks.paste(show(im,bg),(k*cw*2,g*ch*2))
 checks.save(out/'edge-background-check.png')
verify_sources(plan)
report={'coverage':plan['coverage'],'complete_sheets':len(results),'results':results,'sources_reverified':True,'failed_or_pending':[{'name':j['name'],'status':j['status'],'error':j.get('error')} for j in plan['jobs'] if j['status']!='complete'],'metric_limits':'Same prior RGB/low-frequency and motion-relative residual formulas. No optical flow. Native metrics separate from 2x. Background threshold is diagnostic proxy, not semantic segmentation; alpha lock can hide invented outer pixels but cannot correct inside-edge colour or missing thin anatomy. Sheet cells are not temporal model context.'}
write(OUT/'evaluation.json',report)
for r in results:print(r['name'],'2x',round(r['metrics_2x']['motion_relative_residual_delta_mae'],2),'native',round(r['metrics_native']['motion_relative_residual_delta_mae'],2),'contam',round(r['diagnostics']['external_fraction_mean'],3),'border',r['diagnostics']['border_pixels_total'],flush=True)
