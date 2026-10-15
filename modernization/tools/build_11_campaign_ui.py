"""Build/stage/install campaign geometry with owned Manager tutorial-art jobs."""
from pathlib import Path
import argparse,base64,json,shutil,struct,subprocess,time,urllib.request
import numpy as np
from PIL import Image
import build_remastered_11 as b
import seedvr_ui_11 as s
from spr_assets import read_spr,decode
from stage_mixed_ui_v3_sprites import encode
from install_11_minimap_v2 import idle,resources,replace
import os

atomic_replace=replace
def replace(path,raw):
 import gc
 gc.collect()
 if path.suffix.lower()!='.exe':return atomic_replace(path,raw)
 # Windows may deny replace-existing on a PE while allowing its rename.
 temp=path.with_name(path.name+'.campaign-new');parked=path.with_name(path.name+'.campaign-previous')
 if temp.exists() or parked.exists():raise RuntimeError('Unresolved executable transaction')
 temp.write_bytes(raw)
 try:
  os.rename(path,parked);os.rename(temp,path)
 except BaseException:
  if parked.exists() and not path.exists():os.rename(parked,path)
  temp.unlink(missing_ok=True);raise
 parked.unlink()

FIX=b.ROOT/'modernization/build/remastered-1.1-campaign-ui'
BACK=b.ROOT/'modernization/backups/remastered-1.1-campaign-ui'
RT=b.TARGET/'runtime';ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
MODEL='seedvr2_ema_7b_sharp_fp8_e4m3fn.safetensors'
BASE='http://127.0.0.1:8790'

def api(route,payload=None,key=None):
 credential=Path(os.environ['MM_LOCAL_MODEL_CREDENTIAL'])
 headers={'Authorization':'Bearer '+json.loads(credential.read_text())['token'],'Content-Type':'application/json'}
 if key:headers['Idempotency-Key']=key
 req=urllib.request.Request(BASE+route,headers=headers,data=None if payload is None else json.dumps(payload).encode())
 with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)

def art():
 FIX.mkdir(exist_ok=True);path=FIX/'tutorial-jobs.json'
 if path.exists():plan=json.loads(path.read_text())
 else:
  plan={'model':MODEL,'jobs':[],'scope':'UI-only speech boxes1..3 and four tutorial portraits; battle originals unchanged'}
  inputs=[RT/'Speechbox/800x600'/f'Speech800x600-{i}.JPG' for i in range(1,4)]
  inputs += [RT/'Portraits/800x600'/f'{name} 800x600.jpg' for name in ['Realm','Character','Portmanteau','Grimoire']]
  for source in inputs:
   original=Image.open(source).convert('RGB');pixels=np.array(original);pixels[s.keys(original)]=[128,104,72]
   inp=FIX/'model-inputs'/source.name;inp.parent.mkdir(exist_ok=True);Image.fromarray(pixels).save(inp.with_suffix('.PNG'))
   inp=inp.with_suffix('.PNG');rel=source.relative_to(RT).as_posix().replace('800x600/','hd-ui/');output=FIX/'runtime'/Path(rel).with_suffix('.PNG')
   plan['jobs'].append(dict(source=str(source),source_sha256=b.sha(source),input=str(inp),input_sha256=b.sha(inp),size=[v*2 for v in original.size],output=str(output),status='pending'))
  b.write(path,plan)
 for index,job in enumerate(plan['jobs']):
  if job['status']=='complete':continue
  source=Path(job['source']);inp=Path(job['input']);assert b.sha(source)==job['source_sha256'] and b.sha(inp)==job['input_sha256']
  if 'job_id' not in job:
   key='mm11-campaign-tutorial-'+str(index)+'-'+job['input_sha256'][:20];job['idempotency_key']=key;b.write(path,plan)
   result=api('/workbench/api/upscale/image',{'data_url':'data:image/png;base64,'+base64.b64encode(inp.read_bytes()).decode(),'model':MODEL,'width':job['size'][0],'height':job['size'][1],'scale':2},key)
   job.update(job_id=result['job_id'],status='submitted');b.write(path,plan);print('Queued',source.name,job['job_id'],flush=True)
  deadline=time.monotonic()+1200
  while True:
   result=api('/api/jobs/'+job['job_id'])
   if result['state']=='succeeded':
    raw=Path(result['result']['file']).resolve();assert raw.is_relative_to(Path('D:/AI/LocalModelManager/media').resolve())
    saved=FIX/'model-results'/str(index);saved.parent.mkdir(exist_ok=True);shutil.copy2(raw,saved.with_suffix('.PNG'))
    before=Image.open(source).convert('RGB').resize(tuple(job['size']),Image.Resampling.NEAREST)
    enhanced=Image.open(raw).convert('RGB').resize(tuple(job['size']),Image.Resampling.LANCZOS)
    enhanced=guard(enhanced,before);output=Path(job['output']);output.parent.mkdir(parents=True,exist_ok=True);enhanced.save(output)
    job.update(status='complete',raw_output=str(saved.with_suffix('.PNG')),raw_sha256=b.sha(saved.with_suffix('.PNG')),sha256=b.sha(output));b.write(path,plan);print('Saved',output.name,flush=True);break
   if result['state'] in ['failed','cancelled','recovery_required']:raise RuntimeError(str(result.get('error') or result['state']))
   if time.monotonic()>deadline:raise TimeoutError('Resume saved owned job '+job['job_id'])
   time.sleep(3)

def guard(image,before):
 mask=s.keys(before);pixels=np.array(image);old=np.array(before);pixels[mask]=old[mask]
 extra=s.keys(Image.fromarray(pixels))&~mask;pixels[extra]=old[extra]
 result=Image.fromarray(pixels);assert np.array_equal(s.keys(result),mask);return result

def stage():
 import re
 b.verify();FIX.mkdir(exist_ok=True);plan=json.loads(s.PLAN.read_text());taskmap={t['id']:t for t in plan['tasks']}
 rels=['Interface/CharacterScreen/screen (Character Screen).cfg',
       'Interface/BattleEnd/screen (Battle End - Victory).cfg','Interface/BattleEnd/screen (Battle End - Defeat).cfg',
       'Interface/ExperienceProcessing/screen (Experience Processing).cfg']
 records=[]
 for rel in rels:
  source=RT/rel;raw=source.read_bytes()
  def scale_rect(match):return match[1]+b','.join(str(int(x)*2).encode() for x in match[2].split(b','))
  changed,count=re.subn(rb'(Rect2\s*=\s*)(-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+)',scale_rect,raw)
  assert count>0
  out=FIX/'runtime'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(changed)
  records.append(dict(path=rel,kind='config',rectangles=count,before_sha256=b.sha(source),sha256=b.sha(out)))
 for asset in plan['assets']:
  rel=asset['path']
  if not (rel.startswith('Interface/CharacterScreen/800x600/') or rel in [
      'Interface/BattleEnd/800x600/Battle Victory Screen 800-600.JPG',
      'Interface/BattleEnd/800x600/Battle Defeat Screen 800-600.JPG',
      'Interface/ExperienceProcessing/800x600/Experience Processing 800-600.JPG',
      'Interface/MiniMenu/800x600/Realm View Mini Menu 800-600.PNG']):continue
  assert b.sha(RT/rel)==asset['sha256']
  out=FIX/'runtime'/rel;out.parent.mkdir(parents=True,exist_ok=True)
  variant='MiniMenu/' in rel
  if variant:out=FIX/'runtime/Interface/MiniMenu/hd-ui'/Path(rel).name;out.parent.mkdir(parents=True,exist_ok=True)
  if asset['type']=='raster':
   old=Image.open(RT/rel).convert('RGB');size=tuple(v*2 for v in old.size);before=old.resize(size,Image.Resampling.NEAREST)
   model=Path(taskmap[asset['task']]['output']) if asset['task'] else RT/rel
   if asset['task']:assert b.sha(model)==taskmap[asset['task']]['output_sha256']
   canvas=size==(2560,1440)
   image=Image.open(model).convert('RGB').resize((1920,1440) if canvas else size,Image.Resampling.LANCZOS)
   if canvas:
    full=Image.new('RGB',size);full.paste(image,(320,0));image=full
   image=guard(image,before)
   if asset.get('runtime_format')=='JPEG':s.save_jpeg_verified(image,out,before)
   else:image.save(out)
   assert np.array_equal(s.keys(Image.open(out)),s.keys(before))
   record=dict(kind='raster',size=list(size),canvas=canvas,variant=variant)
  else:
   cp,cf=read_spr(RT/rel);images={}
   for atlas in asset['atlases']:
    task=taskmap[atlas['task']];assert b.sha(Path(task['output']))==task['output_sha256'];image=Image.open(task['output']).convert('RGB')
    for cell in atlas['cells']:
     f=cf[cell['index']];size=(f['width']*2,f['height']*2)
     im=image.crop(tuple(v*4 for v in cell['rect'])).resize(size,Image.Resampling.LANCZOS).convert('RGBA')
     im.putalpha(decode(cp,f).getchannel('A').resize(size,Image.Resampling.NEAREST));images[f['index']]=im
   blocks=[encode(f,images.get(f['index'],decode(cp,f).resize((f['width']*2,f['height']*2),Image.Resampling.NEAREST))) for f in cf]
   raw=bytearray((RT/rel).read_bytes()[:24]);struct.pack_into('<II',raw,16,0,0);position=0
   for block in blocks:raw.extend(struct.pack('<I',position));position+=len(block)
   for block in blocks:raw.extend(block)
   struct.pack_into('<I',raw,4,len(raw));out.write_bytes(raw)
   npal,nframes=read_spr(out);assert len(nframes)==len(cf)
   for old,new in zip(cf,nframes):
    assert all(new[k]==old[k]*2 for k in ['width','height']) and new['offset']==[v*2 for v in old['offset']] and new['name']==old['name']
    assert np.array_equal(np.array(decode(npal,new).getchannel('A')),np.array(decode(cp,old).getchannel('A').resize((new['width'],new['height']),Image.Resampling.NEAREST)))
   record=dict(kind='sprite',frames=len(cf),scale=2,alpha_exact=True,variant=False)
  records.append(dict(path=out.relative_to(FIX/'runtime').as_posix(),original_path=rel,before_sha256=None if variant else b.sha(RT/rel),sha256=b.sha(out),**record))
 b.write(FIX/'staged-assets.json',dict(records=records,manifest_before_sha256=b.sha(b.TARGET/'manifest.json'),launcher_before_sha256=b.sha(ENTRY)))
 print('Staged',len(records),'campaign geometry assets/configs')

def build():
 preflight()
 FIX.mkdir(exist_ok=True)
 source=b.ROOT/'modernization/build/remastered-1.1-cursor-full'
 for n in ['qol_bindings.cpp','layout_context.h','mixed_ui_fonts.cpp','ui_geometry.h']:shutil.copy2(source/n,FIX/n)
 shutil.copy2(b.SRC/'campaign_ui.cpp',FIX/'campaign_ui.cpp')
 q=(FIX/'qol_bindings.cpp').read_text();needle='return install() && mm_install_mixed_fonts()?TRUE:FALSE;';assert q.count(needle)==1
 q=q.replace('extern "C" bool mm_install_mixed_fonts();','extern "C" bool mm_install_mixed_fonts();\nextern "C" bool mm_install_campaign_ui();')
 q=q.replace(needle,'return install() && mm_install_mixed_fonts() && mm_install_campaign_ui()?TRUE:FALSE;');(FIX/'qol_bindings.cpp').write_text(q)
 latest=b.ROOT/'modernization/build/remastered-1.1-grimoire-load'
 for n in ['launcher.cpp','repath.dll','combined.rc']:shutil.copy2(latest/n,FIX/n)
 assert resources(ENTRY)[101]==(FIX/'repath.dll').read_bytes()
 cmd='@echo off\ncall "'+str(b.VC)+'" x86 >nul\nif errorlevel 1 exit /b 1\n'
 cmd+='cl /nologo /LD /O2 /EHsc /std:c++17 /W4 qol_bindings.cpp mixed_ui_fonts.cpp campaign_ui.cpp /link /OUT:qol_bindings.dll /MAP:qol_bindings.map user32.lib\nif errorlevel 1 exit /b 1\n'
 cmd+='rc /nologo /focandidate.res combined.rc\nif errorlevel 1 exit /b 1\n'
 cmd+='cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:MagicMayhem-Remastered-1.1.exe bcrypt.lib user32.lib\n'
 (FIX/'build.cmd').write_text(cmd);subprocess.run(['cmd','/c','build.cmd'],cwd=FIX,check=True)
 b.write(FIX/'build.json',dict(launcher_sha256=b.sha(FIX/ENTRY.name),qol_sha256=b.sha(FIX/'qol_bindings.dll'),sources={p.name:b.sha(p) for p in FIX.glob('*.cpp')}))

def preflight():
 import re,pefile
 engine=RT/'Chaos-Wide169-engine.exe'
 assert b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 pe=pefile.PE(str(engine));image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
 source=(b.SRC/'campaign_ui.cpp').read_text();checked=[]
 for address,before,after in re.findall(r'\{(0x[0-9a-f]+),(\d+),(\d+)\}',source):
  address=int(address,16);assert struct.unpack_from('<I',image,address-base)[0]==int(before),hex(address);checked.append(hex(address))
 for address,target in re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),\(void\*\)',source):
  address=int(address,16);target=int(target,16);assert image[address-base]==0xe8 and address+5+struct.unpack_from('<i',image,address-base+1)[0]==target;checked.append(hex(address))
 assert image[0x4b221f-base:0x4b2224-base]==bytes.fromhex('8bceff501c')
 assert image[0x572f30-base:0x572f37-base]==bytes.fromhex('6aff683b2c5c00')
 png=pefile.PE(str(RT/'png_pages.dll'));assert b'@mm_png_page@12' in [symbol.name for symbol in png.DIRECTORY_ENTRY_EXPORT.symbols]
 FIX.mkdir(exist_ok=True);b.write(FIX/'preflight.json',dict(engine_sha256=b.sha(engine),sites=checked+['0x4b221f','0x572f30'],png_export='@mm_png_page@12',disk_engine_unchanged=True))

def install():
 idle();b.verify();preflight();stageinfo=json.loads((FIX/'staged-assets.json').read_text());assert b.sha(ENTRY)==stageinfo['launcher_before_sha256']
 assert b.sha(b.TARGET/'manifest.json')==stageinfo['manifest_before_sha256']
 tutorial=json.loads((FIX/'tutorial-jobs.json').read_text());assert all(j['status']=='complete' for j in tutorial['jobs'])
 assert resources(ENTRY)[101]==resources(FIX/ENTRY.name)[101]
 m=json.loads((b.TARGET/'manifest.json').read_text());plan=json.loads(s.PLAN.read_text());updates={ENTRY:(FIX/ENTRY.name).read_bytes()}
 for record in stageinfo['records']:
  target=RT/record['path'];assert (b.sha(target) if target.exists() else None)==record['before_sha256']
  updates[target]=(FIX/'runtime'/record['path']).read_bytes();m['files'][record['path']]=record['sha256']
  if record['kind'] in ['raster','sprite'] and not record['variant']:
   asset=next(a for a in plan['assets'] if a['path']==record['path'])
   output=Path(asset['output']);updates[output]=updates[target]
   asset.update(sha256=record['sha256'],geometry_scale=2,derivative_override=str(FIX/'runtime'/record['path']),derivative_override_sha256=record['sha256'])
   if record['kind']=='raster':
    asset.update(size=record['size'],content_size=[1920,1440] if record['canvas'] else record['size'],canvas=record['canvas'])
    if asset.get('runtime_format')=='JPEG':updates[output.with_suffix('.PNG')]=(FIX/'runtime'/record['path']).with_suffix('.PNG').read_bytes()
 for job in tutorial['jobs']:
  rel=Path(job['output']).relative_to(FIX/'runtime').as_posix().replace('Speechbox/','SpeechBox/')
  target=RT/rel;assert not target.exists()
  assert b.sha(Path(job['output']))==job['sha256'];updates[target]=Path(job['output']).read_bytes();m['files'][target.relative_to(RT).as_posix()]=job['sha256']
 m['launcher_sha256']=b.sha(FIX/ENTRY.name)
 m['campaign_ui_geometry']=dict(backup=str(BACK),geometry_records=len(stageinfo['records']),tutorial_assets=len(tutorial['jobs']),engine_unchanged=True,resource101_unchanged=True,acceptance='offline checks passed; test16 and user acceptance pending')
 updates[b.TARGET/'manifest.json']=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
 updates[s.PLAN]=(json.dumps(plan,ensure_ascii=False,indent=2)+'\n').encode()
 BACK.mkdir(exist_ok=False);before={p:p.read_bytes() if p.exists() else None for p in updates}
 for p,raw in before.items():
  if raw is not None:
   out=BACK/'project'/p.relative_to(b.ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
 receipt={'files':[dict(path=p.relative_to(b.ROOT).as_posix(),before_sha256=b.sha(p) if raw is not None else None,sha256=__import__('hashlib').sha256(updates[p]).hexdigest()) for p,raw in before.items()]}
 b.write(BACK/'installation.json',receipt)
 try:
  for p,raw in updates.items():p.parent.mkdir(parents=True,exist_ok=True);replace(p,raw)
  b.verify()
 except BaseException:
  for p,raw in before.items():
   if raw is None:p.unlink(missing_ok=True)
   else:replace(p,raw)
  raise
 print('Installed campaign UI checkpoint; scoped test16 authorized')

def rollback():
 idle();state=json.loads((BACK/'installation.json').read_text())
 for row in state['files']:assert b.sha(b.ROOT/row['path'])==row['sha256']
 for row in state['files']:
  target=b.ROOT/row['path']
  if row['before_sha256'] is None:target.unlink()
  else:replace(target,(BACK/'project'/row['path']).read_bytes())
 b.verify()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['art','stage','build','preflight','install','rollback']);globals()[p.parse_args().action]()
