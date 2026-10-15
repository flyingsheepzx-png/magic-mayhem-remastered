"""CPU-only all saved Phoenix treatments, identical CRT kernel and real 2x/4x outputs."""
import ast,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from run_expanded import OUT,write,sha
dest=OUT/'Phoenix/all-renderings-crt';dest.mkdir(exist_ok=True)
kernel_path=OUT/'full_crt_lottes.py';tree=ast.parse(kernel_path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['linear','srgb','render']]
kernel=ast.Module(body=nodes,type_ignores=[]);code=ast.unparse(kernel);(dest/'crt_kernel.py').write_text('import numpy as np\nfrom PIL import Image\n'+code+'\n')
env={'np':np,'Image':Image};exec(compile(kernel,'crt_kernel','exec'),env)
plan=json.loads((OUT/'manifest.json').read_text());job=next(j for j in plan['jobs'] if j['name']=='Phoenix-PBLD');row=job['frames'][0]
src=Image.open(row['source_png']).convert('RGBA');native_size=src.size;target=(src.width*2,src.height*2)
def load(p):return Image.open(p).convert('RGBA')
variants=[]
def add(label,im,path=None):variants.append((label,im,path))
add('Original native',src,row['source_png'])
lanc=src.resize(target,Image.Resampling.LANCZOS);lanc.putalpha(src.getchannel('A').resize(target,Image.Resampling.NEAREST));add('Lanczos 2x / binary alpha',lanc)
base=OUT/'Phoenix'
for label,path in [
 ('SeedVR grey / strict 2x',base/'PBLD/00-seedvr-2x.png'),
 ('SeedVR grey / native export',base/'PBLD/00-seedvr-native.png'),
 ('SeedVR grey / soft raw',base/'alpha-edge-trial/00-1.png'),
 ('SeedVR grey / fringe repair',base/'alpha-edge-trial/00-2.png'),
 ('SeedVR grey / unmatte',base/'alpha-degrey-trial/00-Unmatte-grey.png'),
 ('SeedVR grey / interior extend',base/'alpha-degrey-trial/00-Interior-colour-extend.png'),
 ('SeedVR transparent / native alpha',base/'transparent-input-trial/00-returned-RGBA.png'),
 ('SeedVR pre-bleed / native alpha',base/'bleed-crt-trial/00-bleed-sr.png')]:add(label,load(path),str(path))
backgrounds=[('green',(58,78,44)),('white','white'),('black','black')];records=[]
for bgname,bg in backgrounds:
 native_panel=[];large_panel=[];gallery=[]
 for k,(label,im,path) in enumerate(variants):
  # All treatments are presented on the same 2x native-sized region.
  region=Image.new('RGBA',(144*2,112*2));position=(28*2,20*2)
  if im.size==native_size:display=im.resize(target,Image.Resampling.NEAREST)
  else:assert im.size==target;display=im
  region.paste(display,position);composite=Image.new('RGB',region.size,bg);composite.paste(region,(0,0),region)
  native=Image.new('RGBA',(144,112));native.paste(src,(28,20))
  # For 2x source variants, shader output scale1 retains exact 2x data dimensions.
  # Use full native original for original arm. Others see their actual upscaled RGB.
  if label=='Original native':
   ci=Image.new('RGB',native.size,bg);ci.paste(native,(0,0),native);env['a']=np.array(ci).astype(float)/255;shader_scale=2
  else:env['a']=np.array(composite).astype(float)/255;shader_scale=1
  exact=env['render'](shader_scale,0);shift=env['render'](shader_scale,.25)
  # 4x native output: original shader2x as prior four-sample view; 2x assets rendered2x.
  env['a']=np.array(composite).astype(float)/255
  crt4=env['render'](2,0)
  if label=='Original native':
   env['a']=np.array(ci).astype(float)/255;crt4=env['render'](4,0)
  folder=dest/f'{k:02d}';folder.mkdir(exist_ok=True)
  for name,img in [('plain-2x',composite),('crt-2x',exact),('crt-2x-phase',shift),('crt-4x',crt4)]:img.save(folder/f'{bgname}-{name}.png')
  # Every source treatment gets a readable row; no image resampling except integer display zoom.
  images=[composite,exact,shift];canvas=Image.new('RGB',(576*3,488),(24,24,30));d=ImageDraw.Draw(canvas)
  for col,(title,img) in enumerate(zip(['No CRT','CRT exact 2x','CRT 2x / phase .25'],images)):
   canvas.paste(img.resize((576,448),Image.Resampling.NEAREST),(576*col,40));d.text((576*col+8,8),label,fill='white');d.text((576*col+8,24),title,fill='white')
  canvas.save(folder/f'{bgname}-comparison-2x.png');native_panel.append(canvas)
  c4=Image.new('RGB',(1152,488),(24,24,30));d=ImageDraw.Draw(c4);c4.paste(composite.resize((576,448),Image.Resampling.NEAREST),(0,40));c4.paste(crt4,(576,40));d.text((8,8),label+' / no CRT display 4x',fill='white');d.text((584,8),'CRT output 4x',fill='white');c4.save(folder/f'{bgname}-comparison-4x.png');large_panel.append(c4)
  if bgname=='green':
   records.append({'ordinal':k,'label':label,'actual_asset_dimensions':im.size,'source':path,'source_sha256':sha(path) if path else None,'data_2x_dimensions':composite.size,'crt4_dimensions':crt4.size,'shader_input_dimensions':native.size if label=='Original native' else composite.size,'shader_scale_2x':shader_scale,'alpha':'saved treatment alpha unchanged; composited BEFORE CRT','warning':'2x asset at exact2x output has shader scale1: mask applies, beam/scanlines need 4x output to have sampling headroom'})
 for name,panels in [('2x',native_panel),('4x',large_panel)]:
  allim=Image.new('RGB',(panels[0].width,sum(p.height for p in panels)))
  for i,p in enumerate(panels):allim.paste(p,(0,i*p.height))
  allim.save(dest/f'contact-{bgname}-{name}.png')
page=['<meta charset="utf-8"><title>All Phoenix renderings + CRT</title><style>body{background:#222;color:white;font:18px sans-serif}.scroll{overflow:auto}img{max-width:none}a{color:#acf}section{margin:45px 0}</style><h1>All Phoenix treatments with CRT: actual 2x and 4x</h1><p>Every image retains saved dimensions; scroll rather than fit-to-window. CRT kernel parameters match previous full Lottes CPU port. 2x asset + 2x output has no extra shader sampling headroom. 4x is diagnostic.</p>']
for r in records:
 k=r['ordinal'];page.append(f'<section><h2>{r["label"]}</h2><p>Asset pixels: {r["actual_asset_dimensions"]}</p><h3>Actual 2x output</h3><div class="scroll"><img src="{k:02d}/green-comparison-2x.png"></div><h3>4x output diagnostic</h3><div class="scroll"><img src="{k:02d}/green-comparison-4x.png"></div><p><a href="{k:02d}/white-comparison-2x.png">White 2x</a> · <a href="{k:02d}/black-comparison-2x.png">Black 2x</a> · <a href="{k:02d}/white-comparison-4x.png">White 4x</a></p></section>')
(dest/'index.html').write_text(''.join(page),encoding='utf-8');write(dest/'manifest.json',{'variants':records,'kernel_source_sha256':sha(kernel_path),'kernel_extracted_sha256':sha(dest/'crt_kernel.py'),'frames':'Phoenix PBLD0001, same frame throughout','gpu_jobs':0,'runtime_changed':False,'crt_parameters_reference':'../full-crt-lottes/parameters.json','limits':'Static comparison; no gameplay/motion acceptance. Original+CRT and SR+CRT differ in shader input resolution. Original outputs from Bat multi-model study are not Phoenix renders and are excluded.'})
print('Complete',len(variants),'variants; 3 backgrounds; 2x and 4x outputs')
