"""Manager RGBA colour-bleed SR + CPU Lottes-derived light beam display experiment."""
import json,time,base64,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from run_expanded import OUT,api,sha,write,verify_sources
plan=json.loads((OUT/'manifest.json').read_text());verify_sources(plan);job=next(j for j in plan['jobs'] if j['name']=='Phoenix-PBLD')
dest=OUT/'Phoenix/bleed-crt-trial';dest.mkdir(exist_ok=True);ledger=dest/'manifest.json'
if ledger.exists():record=json.loads(ledger.read_text())
else:
 sheet=Image.new('RGBA',tuple(job['input_size']));cw,ch=job['cell_size']
 for row in job['frames']:
  im=Image.open(row['source_png']).convert('RGBA');a=np.zeros((ch,cw,4),dtype=np.uint8);x,y=row['local_position'];a[y:y+im.height,x:x+im.width]=np.array(im)
  ys,xs=np.where(a[:,:,3]>0)
  # Transparent pixels retain alpha0; fill hidden RGB from nearest subject donor across each isolated cell.
  for yy in range(ch):
   for xx in range(cw):
    if a[yy,xx,3]==0:
     k=int(((ys-yy)**2+(xs-xx)**2).argmin());a[yy,xx,:3]=a[ys[k],xs[k],:3]
  sheet.paste(Image.fromarray(a),tuple(row['cell_origin']))
 inp=dest/'input-rgba-colour-bleed.png';sheet.save(inp);record={'input':str(inp),'input_sha256':sha(inp),'source_sha256':job['source_sha256'],'method':'all alpha-zero RGB filled from nearest source opaque pixel within its cell, BEFORE inference; alpha unmodified','profile':'seed42/noise0/Lab/batch1/tiledVAE/CPUoffload','target_size':job['target_size'],'model':plan['model'],'status':'prepared'};write(ledger,record)
if 'job_id' not in record:
 key='phoenix-prebleed-'+record['input_sha256'][:24];record['idempotency_key']=key;write(ledger,record)
 response=api('/workbench/api/upscale/image',{'data_url':'data:image/png;base64,'+base64.b64encode(Path(record['input']).read_bytes()).decode(),'model':record['model'],'width':job['target_size'][0],'height':job['target_size'][1],'scale':2},key);record.update(job_id=response['job_id'],status='submitted');write(ledger,record);print('SAVED',record['job_id'],flush=True)
deadline=time.monotonic()+1200
while record['status']!='complete':
 j=api('/api/jobs/'+record['job_id']);print(j['state'],flush=True)
 if j['state']=='succeeded':
  source=Path(j['result']['file']).resolve();assert source.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve());output=dest/'returned-rgba.png';shutil.copy2(source,output);im=Image.open(output);assert im.mode=='RGBA' and list(im.size)==job['target_size'];record.update(status='complete',output=str(output),output_sha256=sha(output));write(ledger,record);break
 if j['state'] in ['failed','cancelled','recovery_required']:raise RuntimeError(str(j))
 if time.monotonic()>deadline:raise TimeoutError('Resume saved ID')
 time.sleep(3)
raw=Image.open(record['output']).convert('RGBA')
def srgb_to_linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def linear_to_srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def crt(im,scan_strength):
 # CPU adaptation of Lottes Gaussian horizontal/vertical beam weights. No warp, phosphor mask, bloom.
 src=srgb_to_linear(np.array(im).astype(float)/255);h,w=src.shape[:2];ox=(np.arange(w*2)+.5)/2;oy=(np.arange(h*2)+.5)/2;ix=np.floor(ox).astype(int);iy=np.floor(oy).astype(int);dx=.5-(ox%1);dy=.5-(oy%1)
 result=np.zeros((h*2,w*2,3));vertical_sum=np.zeros(h*2)
 for yy in [-1,0,1]:
  horizontal=np.zeros_like(result);den=np.zeros(w*2)
  for xx in [-2,-1,0,1,2]:
   weight=2**(-6*(dx+xx)**2);horizontal+=src[np.clip(iy+yy,0,h-1)[:,None],np.clip(ix+xx,0,w-1)[None,:]]*weight[None,:,None];den+=weight
  horizontal/=den[None,:,None];weight=2**(-8*(dy+yy)**2);result+=horizontal*weight[:,None,None];vertical_sum+=weight
 # Normalize for beam-only; blend partial unnormalized scanline attenuation for light CRT.
 result/=vertical_sum[:,None,None];atten=(1-scan_strength)+scan_strength*vertical_sum/vertical_sum.max();result*=atten[:,None,None]
 return Image.fromarray(np.rint(linear_to_srgb(result).clip(0,1)*255).astype('uint8'))
labels=['Original nearest 2x','Original beam only','Original light CRT','Old transparent SR','Pre-bleed transparent SR'];notes=[]
for bgname,bg in [('white','white'),('black','black'),('grey',(48,48,56))]:
 frames=[]
 for row in job['frames']:
  i=row['ordinal'];src=Image.open(row['source_png']).convert('RGBA');x,y=[v*2 for v in row['local_position']];ox,oy=[v*2 for v in row['cell_origin']];w,h=src.width*2,src.height*2;new=raw.crop((ox+x,oy+y,ox+x+w,oy+y+h));new.save(dest/f'{i:02d}-bleed-sr.png');old=Image.open(OUT/'Phoenix/transparent-input-trial'/f'{i:02d}-returned-RGBA.png').convert('RGBA')
  # CRT operates on background-composited native pixels (not transparent sprite channels).
  native=Image.new('RGB',src.size,bg);native.paste(src,(0,0),src)
  displays=[native.resize((w,h),Image.Resampling.NEAREST),crt(native,0),crt(native,.2)]
  for im in [old,new]:
   c=Image.new('RGB',im.size,bg);c.paste(im,(0,0),im);displays.append(c)
  zoom=3;canvas=Image.new('RGB',(w*zoom*len(labels),h*zoom+50),bg);d=ImageDraw.Draw(canvas)
  for col,(label,im) in enumerate(zip(labels,displays)):canvas.paste(im.resize((w*zoom,h*zoom),Image.Resampling.NEAREST),(col*w*zoom,50));d.text((col*w*zoom+5,8),label,fill='#ff00ff');d.text((col*w*zoom+5,25),row['name']+' / 2x, display3x',fill='#ff00ff')
  canvas.save(dest/f'frame-{i:02d}-{bgname}.png')
  # Native dimensions differ across frames: use fixed canvas for valid APNG.
  padded=Image.new('RGB',(1260*3,180*3+50),bg);padded.paste(canvas,(0,0));frames.append(padded)
 frames[0].save(dest/f'animation-{bgname}.png',save_all=True,append_images=frames[1:],duration=125,loop=0)
record['crt']={'implementation':'CPU Lottes-derived Gaussian beam approximation; not execution of full community GPU shader','horizontal_hardness':-6,'vertical_hardness':-8,'scan_strengths':[0,.2],'linear_srgb':True,'warp':False,'mask':False,'bloom':False,'input':'source sprite composited on test background; not actual battle scene','scale':2};write(ledger,record);verify_sources(plan)
(dest/'index.html').write_text('<meta charset="utf-8"><style>body{background:#222;color:white}.scroll{overflow:auto}img{max-width:none}</style><h1>Phoenix pre-inference bleed / light CRT</h1>'+''.join('<h2>'+b+'</h2><div class="scroll"><img src="frame-00-'+b+'.png"></div><a href="animation-'+b+'.png">8 frame APNG</a>' for b in ['white','black','grey']),encoding='utf-8')
print('Comparison ready',flush=True)
