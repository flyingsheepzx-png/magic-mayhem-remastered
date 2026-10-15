"""One fresh Qwen crop trial and source-protected offline compositing only.
All writes in this directory. No credentials, game calls, or queue mutations.
"""
import argparse, json, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import run_trials as t
from evaluate_trials import contact, gray, shifted_match
NAME='03-context-crop-v2'
CROP=(360,240,760,540)
PROMPT=('Perform a minimal restoration of this exact rectangular crop from an old hand-painted Celtic game map. '
'The reference is authoritative. Preserve all existing pixels spatially: identical framing, tree silhouettes, tree height, forest boundaries, cliffs, paths, roads, river banks, lake shore, buildings and clearings. '
'Only gently clarify the already present painted needle/leaf shading INSIDE existing forest canopies and the already present rock shading INSIDE existing cliff faces. '
'Keep existing tall narrow conifers tall and narrow; do not substitute rounded deciduous trees. Keep the original dark green palette and original shadow directions. '
'Consolidate tiny compression-like flecks without creating new individual trees, changing canopy spacing, redrawing terrain, sharpening roads or interpreting architecture. '
'Leave roads, water, shorelines, buildings, landmark objects and open grass exactly as supplied. Keep every feature crossing a crop edge in the same place. '
'No new details outside original silhouettes, no larger objects, no new geometry, no map redesign, no text or markings. A subtle conservative edit, not a new illustration.')
NEGATIVE='redesigned map, different geography, new trees, round deciduous canopy, displaced trees, new rocks, new buildings, changed roads, moved shore, different lighting, changed color palette, labels, text, grain, stippling, oversharpening'
t.CONFIG[NAME]={'size':'1024x768','seed':26093031,'crop':CROP,'prompt':PROMPT}
t.NEGATIVE=NEGATIVE

def generate():
 before=t.verify(); t.write_json(NAME+'-preflight.json',before)
 im=Image.open(t.SOURCE).convert('RGB').crop(CROP)
 im.save(t.ROOT/(NAME+'-reference-400x300.png'))
 im.resize((960,720),t.LANCZOS).save(t.ROOT/(NAME+'-reference-target.png'))
 t.write_json(NAME+'-settings.json',{'model':'Qwen-Image 2.1','candidate':NAME,'crop_source_box':CROP,'reference_size':[400,300],'model_size':'1024x768','comparison_target_size':[960,720],'seed':26093031,'steps':40,'official_prompt_enhance':False,'prompt':PROMPT,'negative_prompt':NEGATIVE,'max_waiting_gpu_seconds':180,'max_total_poll_seconds':600,'structure_control':'reference image and conservative prompt only; no model hard mask or denoise parameter exposed'})
 original_api=t.api; start=time.monotonic(); waiting_since=None
 def bounded_api(route,payload=None):
  nonlocal waiting_since
  result=original_api(route,payload)
  if payload is None and route.startswith('/api/keyframe2/jobs/'):
   job=result.get('job',{}); status=job.get('status'); phase=job.get('phase_code') or job.get('phase')
   terminal=status in {'completed','failed','canceled','cancelled','interrupted'}
   waiting=status in {'queued','pending'} or phase=='waiting_gpu'
   if waiting and waiting_since is None: waiting_since=time.monotonic()
   if not waiting: waiting_since=None
   reason=None
   if not terminal and waiting_since is not None and time.monotonic()-waiting_since>180: reason='Continuous GPU queue wait exceeded 180 seconds'
   if not terminal and time.monotonic()-start>600: reason='Total managed job polling exceeded 600 seconds'
   if reason:
    job_id=route.rsplit('/',1)[1]; original_api('/api/keyframe2/jobs/'+job_id+'/cancel',{})
    t.write_json(NAME+'-blocker.json',{'manager_job_id':job_id,'reason':reason,'last_status':status,'last_phase':phase,'elapsed_seconds':round(time.monotonic()-start,2),'action':'cancel only owned job; no resubmission'})
    raise TimeoutError(reason)
  return result
 t.api=bounded_api
 try: t.generate(NAME)
 finally: t.api=original_api

def evaluate():
 before=t.load_json(NAME+'-preflight.json'); current=t.verify()
 src=Image.open(t.SOURCE).convert('RGB'); base=src.resize((1920,1440),t.LANCZOS)
 box=tuple(round(v*2.4) for v in CROP)
 reference=base.crop(box)
 reference.save(t.ROOT/(NAME+'-reference-target.png'))
 raw=Image.open(t.ROOT/(NAME+'-raw.png')).convert('RGB'); candidate=raw.resize((960,720),t.LANCZOS)
 candidate.save(t.ROOT/(NAME+'-target.png'))
 box=tuple(round(v*2.4) for v in CROP)
 old=Image.open(t.OLD).convert('RGB').crop(box)
 # Deliberately small, hand-picked canopy/rock interiors in source coordinates.
 # Narrow masks protect roads, lake, settlement and the coast; saved masks are reviewable.
 forest=[(556,333,602,369),(575,396,622,438),(651,344,690,380)]
 rock=[(457,421),(467,414),(479,414),(481,425),(470,434),(460,430)]
 mask=Image.new('L',(960,720),0); draw=ImageDraw.Draw(mask)
 def point(pt): return (round((pt[0]-CROP[0])*2.4),round((pt[1]-CROP[1])*2.4))
 for b in forest:
  a=point(b[:2]); z=point(b[2:]); draw.ellipse((*a,*z),fill=255)
 draw.polygon([point(p) for p in rock],fill=255)
 # Clip feather to support so excluded pixels stay exactly source-derived.
 support=np.asarray(mask); feather=np.asarray(mask.filter(ImageFilter.GaussianBlur(7)))
 m=np.minimum(support,feather).astype('uint8'); mask=Image.fromarray(m); mask.save(t.ROOT/(NAME+'-local-mask.png'))
 ref=np.asarray(reference,dtype=np.float32); gen=np.asarray(candidate,dtype=np.float32)
 # Source broad geometry/color remain intact; permit moderate local detail residual only.
 hi_ref=ref-np.asarray(reference.filter(ImageFilter.GaussianBlur(5)),dtype=np.float32)
 hi_gen=gen-np.asarray(candidate.filter(ImageFilter.GaussianBlur(5)),dtype=np.float32)
 residual=np.clip(hi_gen-hi_ref,-24,24); alpha=m[:,:,None].astype(np.float32)/255.*.65
 blended=Image.fromarray(np.clip(np.rint(ref+residual*alpha),0,255).astype('uint8'))
 blended.save(t.ROOT/(NAME+'-protected-target.png'))
 full=base.copy(); full.paste(blended,(box[0],box[1])); full.save(t.ROOT/(NAME+'-protected-full-1920x1440.png'))
 fullmask=Image.new('L',base.size,0); fullmask.paste(mask,(box[0],box[1])); fullmask.save(t.ROOT/(NAME+'-full-mask.png'))
 raw_mount=base.copy(); raw_mount.paste(candidate,(box[0],box[1])); raw_mount.save(t.ROOT/(NAME+'-raw-mounted-full.png'))
 items=[('Source nearest',src.crop(CROP).resize((960,720),Image.Resampling.NEAREST)),('Source Lanczos',reference),('Old Qwen',old),('03-v2 raw target',candidate),('03-v2 protected',blended)]
 contact(NAME+'-context-comparison.png',items,width=480)
 regions={'forest':(round((545-360)*2.4),round((320-240)*2.4),round((645-360)*2.4),round((445-240)*2.4)), 'rock':(round((432-360)*2.4),round((390-240)*2.4),round((495-360)*2.4),round((465-240)*2.4)), 'protected-lake-road':(0,0,336,264)}
 for key,b in regions.items(): contact(NAME+'-'+key+'-1to1.png',items,b,width=None)
 small=candidate.resize((400,300),t.LANCZOS); srcg=gray(src.crop(CROP).filter(ImageFilter.GaussianBlur(1.2))); geng=gray(small.filter(ImageFilter.GaussianBlur(1.2)))
 regions_source={'lake-edge':(48,12,120,65),'forest':(195,100,243,144),'rock':(89,169,128,202),'east-coast':(338,176,380,220)}
 delta=np.abs(np.asarray(full,dtype=np.int16)-np.asarray(base,dtype=np.int16)); outside=np.asarray(fullmask)==0
 local_delta=np.abs(np.asarray(blended,dtype=np.int16)-ref)
 assert int(delta[outside].max())==0, 'Protection violated outside mask'
 measured={'source_sha256':current['source_sha256'],'queue_sha256_before':before['queue_sha256'],'queue_sha256_after':current['queue_sha256'],'queue_unchanged':current['queue_sha256']==before['queue_sha256'],'old_output_unchanged':current['old_sha256']==before['old_sha256'],'raw_crop_mean_abs_rgb_vs_lanczos':float(np.mean(np.abs(gen-ref))),'raw_crop_lowpass_rgb_difference':float(np.mean(np.abs(np.asarray(candidate.filter(ImageFilter.GaussianBlur(12)),dtype=np.float32)-np.asarray(reference.filter(ImageFilter.GaussianBlur(12)),dtype=np.float32)))),'protected_max_rgb_delta_outside_mask':int(delta[outside].max()),'protected_max_rgb_delta':int(delta.max()),'changed_full_image_fraction':float(np.mean(np.any(delta!=0,axis=2))),'raw_structure_correlation':{k:shifted_match(srcg,geng,b) for k,b in regions_source.items()},'method':{'forest_source_ellipses':forest,'rock_source_polygon':rock,'gaussian_highpass_radius_target_px':5,'feather_radius_target_px':7,'residual_clip_rgb':24,'blend':.65,'base':'original Lanczos; not old Qwen','hard_structure_control':'CPU spatial exclusion only; model request has no hard mask'},'scope':'Offline art only. Protect excluded geometry exactly against source Lanczos. Interior semantic invention still possible.'}
 t.write_json(NAME+'-evaluation.json',measured)
 print(json.dumps(measured,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('mode',choices=['generate','evaluate']); a=p.parse_args()
 generate() if a.mode=='generate' else evaluate()


