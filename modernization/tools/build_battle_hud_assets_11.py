"""Local Manager SeedVR portrait atlas plus approved spell derivatives."""
from pathlib import Path
import argparse,json,struct,base64,time
import numpy as np
from PIL import Image
import seedvr_ui_11 as sr
from spr_assets import read_spr,decode
ROOT=sr.ROOT;OUT=ROOT/'modernization/assets/hd/battle-hud-1.1';PLAN=OUT/'plan.json'
RT=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime')

def prepare():
 if PLAN.exists():return
 OUT.mkdir(exist_ok=False);atlas=Image.new('RGB',(512,512),(128,104,72));rows=[];x=y=8;rowh=0
 for p in sorted((RT/'Bitmaps').glob('*.PNG')):
  if not ('face' in p.stem.lower() or 'cornelius' in p.stem.lower()):continue
  im=Image.open(p).convert('RGB');original=sr.ORIG/'Bitmaps'/(p.stem+'.bmp')
  assert original.exists() and Image.open(original).convert('RGB').tobytes()==im.tobytes()
  if x+im.width+8>512:x=8;y+=rowh+16;rowh=0
  assert y+im.height+8<=512
  a=np.array(im);a[sr.keys(im)]=[128,104,72];atlas.paste(Image.fromarray(a),(x,y))
  rows.append(dict(name=p.name,source=str(original),source_sha256=sr.sha(original),rect=[x,y,x+im.width,y+im.height]))
  x+=im.width+16;rowh=max(rowh,im.height)
 atlas.save(OUT/'portrait-input.png')
 sr.save(PLAN,dict(model=sr.MODEL,input_sha256=sr.sha(OUT/'portrait-input.png'),portraits=rows,status='prepared'))

def generate():
 prepare();p=json.loads(PLAN.read_text());assert sr.sha(OUT/'portrait-input.png')==p['input_sha256']
 if p['status']=='complete':return
 if not p.get('job_id'):
  j=sr.api('/workbench/api/upscale/image',dict(data_url='data:image/png;base64,'+base64.b64encode((OUT/'portrait-input.png').read_bytes()).decode(),model=sr.MODEL,width=2048,height=2048),'mm11-battle-portraits-'+p['input_sha256']+'-'+str(p.get('attempt',1)))
  p.update(job_id=j['job_id'],status='submitted');sr.save(PLAN,p)
 while True:
  j=sr.api('/api/jobs/'+p['job_id']);print(j['state'],flush=True)
  if j['state']=='succeeded':
   source=Path(j['result']['file']).resolve();assert source.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve())
   (OUT/'portrait-result.png').write_bytes(source.read_bytes());p.update(status='complete',output_sha256=sr.sha(OUT/'portrait-result.png'));sr.save(PLAN,p);break
  if j['state'] in ['failed','cancelled','recovery_required']:raise RuntimeError(j['state'])
  time.sleep(5)

def rgb565(im):
 a=np.array(im.convert('RGB')).astype(np.uint16)
 return (((a[:,:,0]>>3)<<11)|((a[:,:,1]>>2)<<5)|(a[:,:,2]>>3)).astype('<u2')

def extend():
 p=json.loads(PLAN.read_text());assert p['status']=='complete'
 if not p.get('extra_input_sha256'):
  known={r['name'] for r in p['portraits']};atlas=Image.new('RGB',(512,512),(128,104,72));x=y=8;rows=[]
  for f in sorted((RT/'Bitmaps').glob('*.PNG')):
   im=Image.open(f).convert('RGB')
   if f.name in known or im.size!=(164,80):continue
   original=sr.ORIG/'Bitmaps'/(f.stem+'.bmp');assert Image.open(original).convert('RGB').tobytes()==im.tobytes()
   if x+im.width+8>512:x=8;y+=96
   assert y+im.height+8<=512
   a=np.array(im);a[sr.keys(im)]=[128,104,72];atlas.paste(Image.fromarray(a),(x,y))
   rows.append(dict(name=f.name,source=str(original),source_sha256=sr.sha(original),rect=[x,y,x+164,y+80],atlas='extra'));x+=180
  atlas.save(OUT/'portrait-extra-input.png');p['portraits']+=rows;p['extra_input_sha256']=sr.sha(OUT/'portrait-extra-input.png');sr.save(PLAN,p)
 if p.get('extra_complete'):return
 if not p.get('extra_job_id'):
  j=sr.api('/workbench/api/upscale/image',dict(data_url='data:image/png;base64,'+base64.b64encode((OUT/'portrait-extra-input.png').read_bytes()).decode(),model=sr.MODEL,width=2048,height=2048),'mm11-battle-portraits-extra-'+p['extra_input_sha256'])
  p['extra_job_id']=j['job_id'];sr.save(PLAN,p)
 while True:
  j=sr.api('/api/jobs/'+p['extra_job_id']);print(j['state'],flush=True)
  if j['state']=='succeeded':
   source=Path(j['result']['file']).resolve();assert source.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve())
   (OUT/'portrait-extra-result.png').write_bytes(source.read_bytes());p.update(extra_complete=True,extra_output_sha256=sr.sha(OUT/'portrait-extra-result.png'));sr.save(PLAN,p);break
  if j['state'] in ['failed','cancelled','recovery_required']:raise RuntimeError(j['state'])
  time.sleep(5)

def pack(spell_only=False):
 p=json.loads(PLAN.read_text())
 if not spell_only:
  assert p['status']=='complete' and sr.sha(OUT/'portrait-result.png')==p['output_sha256']
  result=Image.open(OUT/'portrait-result.png').convert('RGB');assert result.size==(2048,2048)
 entries=[];png=OUT/'png';png.mkdir(exist_ok=True)
 for row in ([] if spell_only else p['portraits']):
  canvas=result
  if row.get('atlas')=='extra':
   assert p.get('extra_complete') and sr.sha(OUT/'portrait-extra-result.png')==p['extra_output_sha256'];canvas=Image.open(OUT/'portrait-extra-result.png').convert('RGB')
  original=Image.open(row['source']).convert('RGB');hi=canvas.crop(tuple(v*4 for v in row['rect'])).resize((original.width*2,original.height*2),Image.Resampling.LANCZOS)
  a=np.array(hi);mask=sr.keys(original);a[np.repeat(np.repeat(mask,2,0),2,1)]=[0,0,255];hi=Image.fromarray(a);hi.save(png/row['name'])
  # Sheets have alive/dead halves separated by one column on teammates.
  width=original.width//2
  for state,x in enumerate([0,original.width-width]):
   lo=original.crop((x,0,x+width,original.height));large=hi.crop((2*x,0,2*(x+width),2*original.height))
   entries.append((1,lo,large,~sr.keys(lo),row['name']+':'+str(state)))
   if width==82:
    # Main HUD mana/health rings overwrite the sheet's outer border. Match
    # only the face core as an additional template, preserving native rings.
    core=(20,10,62,74);small=lo.crop(core);big=large.crop(tuple(v*2 for v in core))
    entries.append((3,small,big,~sr.keys(small),row['name']+':'+str(state)+':face-core'))
 palette,frames=read_spr(RT/'Sprites/SplIcons.spr');hp,hf=read_spr(RT/'Sprites/port-icons.spr')
 for i,(f,h) in enumerate(zip(frames,hf)):
  # Small narrow frames are native charge/meter overlays; retain them as
  # dynamic UI, never mistake one of them for the complete spell portrait.
  if i<3 or f['width']<36 or f['height']<36:continue
  lo=decode(palette,f);hi=decode(hp,h)
  assert hi.size==(lo.width*2,lo.height*2)
  entries.append((2,lo,hi,np.array(lo.getchannel('A'))>0,'spell:'+str(i)))
 entries.sort(key=lambda e:(-(e[1].width*e[1].height),-int(e[3].sum())))
 raw=bytearray(struct.pack('<4sII',b'HDH1',1,len(entries)));records=[]
 for kind,lo,hi,mask,name in entries:
  w,h=lo.size;low=rgb565(lo);high=rgb565(hi)
  points=np.argwhere(mask)
  assert len(points)>0
  anchors=points[np.linspace(0,len(points)-1,24,dtype=int)]
  # Fixed header: kind,width,height +24 linear pixel indexes.
  raw.extend(struct.pack('<27I',kind,w,h,*[int(y*w+x) for y,x in anchors]))
  raw.extend(low.tobytes());raw.extend(mask.astype('u1').tobytes());raw.extend(high.tobytes())
  records.append(dict(name=name,kind=kind,width=w,height=h,opaque=int(mask.sum())))
 (OUT/'battle-hud.bin').write_bytes(raw);sr.save(OUT/'pack.json',dict(model=p['model'],portraits_complete=not spell_only,pack_sha256=sr.sha(OUT/'battle-hud.bin'),entries=records,alpha='exact nearest original coverage',source_plan=str(PLAN)))
 print('Packed',len(entries),'HUD templates')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','generate','extend','pack']);globals()[p.parse_args().action]()
