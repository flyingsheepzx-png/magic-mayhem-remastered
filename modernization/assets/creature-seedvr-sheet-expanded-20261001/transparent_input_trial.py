"""Actual Manager RGBA-input SeedVR rerun; preserve native returned alpha."""
import json,time,base64,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from run_expanded import OUT,api,sha,write,verify_sources
plan=json.loads((OUT/'manifest.json').read_text());verify_sources(plan)
job=next(j for j in plan['jobs'] if j['name']=='Phoenix-PBLD');dest=OUT/'Phoenix/transparent-input-trial';dest.mkdir(exist_ok=True);ledger=dest/'manifest.json'
if ledger.exists():record=json.loads(ledger.read_text())
else:
 sheet=Image.new('RGBA',tuple(job['input_size']),(0,0,0,0))
 for row in job['frames']:
  im=Image.open(row['source_png']).convert('RGBA');x=row['cell_origin'][0]+row['local_position'][0];y=row['cell_origin'][1]+row['local_position'][1];sheet.paste(im,(x,y))
 inp=dest/'input-transparent.png';sheet.save(inp)
 record={'input':str(inp),'input_sha256':sha(inp),'input_mode':'RGBA','transparent_RGB':[0,0,0],'target_size':job['target_size'],'model':plan['model'],'profile_reference':'../../effective-profile.json','status':'prepared','source_job':job['job_id'],'source_sha256':job['source_sha256']};write(ledger,record)
if 'job_id' not in record:
 inp=Path(record['input']);assert sha(inp)==record['input_sha256'];key='mm-phoenix-transparent-'+record['input_sha256'][:24];record['idempotency_key']=key;write(ledger,record)
 response=api('/workbench/api/upscale/image',{'data_url':'data:image/png;base64,'+base64.b64encode(inp.read_bytes()).decode(),'model':record['model'],'width':job['target_size'][0],'height':job['target_size'][1],'scale':2},key)
 record.update(job_id=response['job_id'],status='submitted');write(ledger,record);print('SAVED OWNED ID',record['job_id'],flush=True)
deadline=time.monotonic()+1200;last=None
if record['status']!='complete':
 while True:
  result=api('/api/jobs/'+record['job_id']);state=result['state']
  if state!=last:print(state,flush=True);last=state
  if state in ['failed','cancelled','recovery_required']:record.update(status=state,error=result.get('error'));write(ledger,record);raise RuntimeError(str(record))
  if state=='succeeded':
   source=Path(result['result']['file']).resolve();assert source.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve());output=dest/'raw-returned.png';shutil.copy2(source,output)
   im=Image.open(output);assert list(im.size)==job['target_size'];record.update(status='complete',output=str(output),output_sha256=sha(output),returned_mode=im.mode);write(ledger,record);break
  if time.monotonic()>deadline:raise TimeoutError('Resume saved owned ID; do not duplicate')
  time.sleep(3)
raw=Image.open(record['output']);print('RETURNED',raw.mode,raw.size,flush=True)
rgba=raw.convert('RGBA');alpha=np.array(rgba)[:,:,3];record['returned_alpha']={'unique_values':int(len(np.unique(alpha))),'zero_pixels':int((alpha==0).sum()),'partial_pixels':int(((alpha>0)&(alpha<255)).sum()),'opaque_pixels':int((alpha==255).sum())}
old=Image.open(job['output']).convert('RGB');frames=[]
for row in job['frames']:
 i=row['ordinal'];x=2*(row['cell_origin'][0]+row['local_position'][0]);y=2*(row['cell_origin'][1]+row['local_position'][1]);w=row['width']*2;h=row['height']*2
 crop=rgba.crop((x,y,x+w,y+h));crop.save(dest/f'{i:02d}-returned-RGBA.png')
 # Old grey-input baseline, no new alpha repair: exact source binary mask.
 before=old.crop((x,y,x+w,y+h)).convert('RGBA');before.putalpha(Image.open(row['source_png']).getchannel('A').resize((w,h),Image.Resampling.NEAREST))
 frames.append((before,crop))
for bgname,bg in [('white','white'),('black','black'),('grey',(48,48,56))]:
 animations=[];cw,ch=job['cell_size'];zoom=2
 for i,(before,after) in enumerate(frames):
  row=job['frames'][i];c=Image.new('RGB',(cw*2*zoom*2,ch*2*zoom+40),bg);d=ImageDraw.Draw(c)
  for col,(label,im) in enumerate([('OLD grey input / binary alpha',before),('NEW transparent input / returned alpha',after)]):
   a=Image.new('RGBA',(cw*2,ch*2));a.paste(im,tuple(v*2 for v in row['local_position']));rgb=Image.new('RGB',a.size,bg);rgb.paste(a,(0,0),a);c.paste(rgb.resize((cw*2*zoom,ch*2*zoom),Image.Resampling.NEAREST),(col*cw*2*zoom,40));d.text((col*cw*2*zoom+8,8),label,fill='#ff00ff');d.text((col*cw*2*zoom+8,23),row['name'],fill='#ff00ff')
  c.save(dest/f'frame-{i:02d}-{bgname}.png');animations.append(c)
 animations[0].save(dest/f'animation-{bgname}.png',save_all=True,append_images=animations[1:],duration=125,loop=0)
record['no_postprocessing']='Returned RGBA alpha used unchanged; no unmatting, donor extension or replacement source alpha';write(ledger,record);verify_sources(plan);print(record['returned_alpha'])
