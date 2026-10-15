"""Bounded read-only-input icon review; writes exclusively to its ART sidecar."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,base64,hashlib,json,struct,time,urllib.request,urllib.parse
import numpy as np
from PIL import Image,ImageDraw
from spr_assets import read_spr,decode
from stage_mixed_ui_v3_sprites import encode
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'modernization/assets/hd/quality-review-1.1/ui-icons-20260930'
SOURCE=ROOT/'modernization/assets/hd/source-original/Sprites/Buttons.spr'
RUNTIME=ROOT/'modernization/playtests/remastered-1.1-p1/runtime'
CURRENT=RUNTIME/'Sprites/Buttons.spr'
BASE='http://127.0.0.1:8790/workbench'
SEED=26093021
PROMPT=('Edit this exact 1024x1024 fantasy toolbar sprite reference sheet. Keep exactly 21 isolated icons in the same three columns and seven rows, same centers, same footprint and silhouettes. Each row is one motif with normal, highlighted and pressed states. Preserve the distinct identity and pose of each existing motif: golden metal character statuettes, books, closed chest, open chest, scroll and wizard motifs as depicted. Restore and redesign internal surfaces for Full Readable game art: clear broad gold and bronze metal planes, recognizable book pages and covers, clear chest lid and hinges, readable character faces and robes. Polished hand-painted fantasy UI, strong coherent forms, restrained bright edges and deep shadows, no gritty noise. Keep same object count, poses, orientation and all transparent silhouette boundaries. Retain flat dark gray background exactly. Do not draw panels, labels, frames or extra decoration. Do not merge or move icons. Improve readability at small toolbar sizes. All three states must depict the same object consistently.')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def api(route,payload=None):
 req=urllib.request.Request(BASE+route,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def flatten(im):
 bg=Image.new('RGBA',im.size,'#303038');bg.alpha_composite(im);return bg.convert('RGB')
def sheet(name,images):
 canvas=Image.new('RGB',(3*180,7*132),'#303038');d=ImageDraw.Draw(canvas)
 for i,im in enumerate(images):
  x=(i%3)*180;y=(i//3)*132;canvas.paste(flatten(im),(x+(180-im.width)//2,y+22));d.text((x+5,y+5),str(i),fill='white')
 canvas.save(OUT/name);return canvas

def prepare():
 OUT.mkdir(parents=True,exist_ok=True)
 assert sha(SOURCE)=='14bc9f870348b8e3df556628de28f5b751748803ba98fc90a6514c7ede47ae23'
 paths={'source':SOURCE,'current':CURRENT,'port-page':RUNTIME/'Sprites/port-icons.spr','mixed-original':RUNTIME/'Sprites/mixed-original/Buttons.spr'}
 records={};sets={};metrics=[]
 sp,sf=read_spr(SOURCE);cp,cf=read_spr(CURRENT);assert len(sf)==len(cf)==21
 for key,path in paths.items():
  if not path.exists():continue
  p,f=read_spr(path);ims=[decode(p,x) for x in f];sets[key]=ims
  folder=OUT/key;folder.mkdir(exist_ok=True)
  for i,im in enumerate(ims):im.save(folder/f'{i:02d}.png')
  records[key]={'path':str(path),'sha256':sha(path),'frames':[{k:x[k] for k in ('index','width','height','offset','name','flags')} for x in f]}
  sheet(key+'-sheet.png',ims)
 nearest=[];lanczos=[]
 for i,(s,c) in enumerate(zip(sf,cf)):
  assert c['offset']==[v*2 for v in s['offset']]
  im=sets['source'][i];size=sets['current'][i].size
  n=im.resize(size,Image.Resampling.NEAREST);l=im.resize(size,Image.Resampling.LANCZOS);l.putalpha(n.getchannel('A'))
  nearest.append(n);lanczos.append(l)
  a=np.array(sets['current'][i]);b=np.array(l);mask=np.array(n.getchannel('A'))>0
  metrics.append({'frame':i,'size_hd':size,'alpha_mismatch_current':int(np.count_nonzero(a[:,:,3]!=b[:,:,3])),'opaque_rgb_mae_current_vs_lanczos':float(np.abs(a[:,:,:3].astype(float)-b[:,:,:3])[mask].mean()),'source_opaque_pixels_hd':int(mask.sum())})
 a=sheet('original-nearest-hd.png',nearest);b=sheet('original-lanczos-hd.png',lanczos);c=sheet('current-hd.png',sets['current'])
 comp=Image.new('RGB',(1620,924));comp.paste(a,(0,0));comp.paste(b,(540,0));comp.paste(c,(1080,0));comp.save(OUT/'comparison-nearest-lanczos-current-hd.png')
 ref=Image.new('RGB',(1024,1024),'#303038');boxes=[]
 for i,im in enumerate(lanczos):
  size=(round(im.width*1.25),round(im.height*1.25));x=round((i%3+.5)*1024/3-size[0]/2);y=round((i//3+.5)*1024/7-size[1]/2)
  ref.paste(flatten(im.resize(size,Image.Resampling.LANCZOS)),(x,y));boxes.append([x,y,x+size[0],y+size[1]])
 ref.save(OUT/'reference-1024.png')
 save('review-metrics.json',{'inputs':records,'columns':['nearest','lanczos','current'],'frames':metrics,'reference_boxes':boxes,'runtime_testing':'not run; user testing only'})
 print(json.dumps({'out':str(OUT),'metrics':metrics}),flush=True)
def generate():
 record_path=OUT/'qwen-call.json';result=OUT/'generated-1024.png'
 if result.exists():print('Existing result; no duplicate submission');return
 engine=api('/api/keyframe2/status').get('engines',{}).get('qwen21',{})
 health={k:engine.get(k) for k in ('ok','assets_ready','model','license')};save('qwen-status.json',health)
 assert engine.get('ok') and engine.get('assets_ready'),'Local Qwen unavailable; no substitute'
 if record_path.exists():
  rec=json.loads(record_path.read_text(encoding='utf-8'));assert rec['request']['prompt']==PROMPT
  if rec.get('terminal_status') in ('failed','canceled','cancelled','interrupted'):raise RuntimeError('Terminal owned job; no resubmission')
  jid=rec['manager_job_id']
 else:
  payload={'engine':'qwen21','reference_images':['data:image/png;base64,'+base64.b64encode((OUT/'reference-1024.png').read_bytes()).decode()],'prompt':PROMPT,'negative_prompt':'text, labels, panels, new icons, extra objects, changed grid, moved icons, grain, noise, merged icons','nickname':'MM bounded ui-icons-20260930','quality':'quality','size':'1024x1024','steps':40,'seed':SEED,'per_round':1,'official_prompt_enhance':False,'transparent':False}
  rec={'request':{k:v for k,v in payload.items() if k!='reference_images'},'reference_sha256':sha(OUT/'reference-1024.png'),'health':health,'observations':[],'submitted_local':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
  jid=api('/api/keyframe2/jobs',payload)['job']['id'];rec['manager_job_id']=jid;save('qwen-call.json',rec)
 print('OWNED JOB',jid,flush=True);start=time.monotonic();last=None
 while True:
  job=api('/api/keyframe2/jobs/'+urllib.parse.quote(jid))['job'];status=job.get('status');phase=job.get('phase_code') or job.get('phase')
  if job.get('prompt'):assert job.get('engine')=='qwen21' and job['prompt']==PROMPT
  if (status,phase)!=last:
   rec['observations'].append({'status':status,'phase':phase,'seconds':round(time.monotonic()-start,1)});save('qwen-call.json',rec);print(rec['observations'][-1],flush=True);last=(status,phase)
  if status in ('completed','failed','canceled','cancelled','interrupted'):break
  if time.monotonic()-start>350:
   api('/api/keyframe2/jobs/'+urllib.parse.quote(jid)+'/cancel',{});rec['terminal_status']='cancel-requested-deadline';save('qwen-call.json',rec);raise TimeoutError('Owned job canceled at bounded deadline')
  time.sleep(2)
 rec['terminal_status']=status;save('qwen-call.json',rec)
 assert status=='completed','Owned trial did not complete'
 media=next(s['primary'] for s in job['sequences'] if s.get('primary'));url=urllib.parse.urljoin('http://127.0.0.1:8790',media['url']);assert url.startswith(BASE+'/api/')
 with urllib.request.urlopen(url,timeout=30) as r:raw=r.read()
 assert raw.startswith(b'\x89PNG\r\n\x1a\n');result.write_bytes(raw)
 rec.update(output_sha256=sha(result),output_size=Image.open(result).size,result_gateway_url=url);save('qwen-call.json',rec);print('SAVED',result,flush=True)
def extract():
 report=json.loads((OUT/'review-metrics.json').read_text(encoding='utf-8'));assert all(sha(Path(v['path']))==v['sha256'] for v in report['inputs'].values()),'Review inputs changed';gen=Image.open(OUT/'generated-1024.png').convert('RGB');assert gen.size==(1024,1024)
 sp,sf=read_spr(SOURCE);cp,cf=read_spr(CURRENT);images=[];payloads=[];checks=[]
 folder=OUT/'generated-frames';folder.mkdir(exist_ok=True)
 for i,(s,c,box) in enumerate(zip(sf,cf,report['reference_boxes'])):
  im=gen.crop(box).resize((c['width'],c['height']),Image.Resampling.LANCZOS).convert('RGBA');mask=decode(sp,s).getchannel('A').resize(im.size,Image.Resampling.NEAREST);im.putalpha(mask);im.save(folder/f'{i:02d}.png');images.append(im)
  raw=bytearray(encode(c,im));struct.pack_into('<2i',raw,12,*c['offset']);payloads.append(bytes(raw))
 sheet('generated-masked-hd.png',images)
 raw=bytearray(CURRENT.read_bytes()[:24]);assert not cp;struct.pack_into('<II',raw,16,0,0);pos=0
 for p in payloads:raw.extend(struct.pack('<I',pos));pos+=len(p)
 for p in payloads:raw.extend(p)
 struct.pack_into('<I',raw,4,len(raw));dest=OUT/'Buttons-qwen-trial.spr';dest.write_bytes(raw)
 p,f=read_spr(dest);assert len(f)==21
 for i,(old,new,im) in enumerate(zip(cf,f,images)):
  assert (old['offset'],old['name'],old['width'],old['height'])==(new['offset'],new['name'],new['width'],new['height'])
  actual=np.array(decode(p,new));want=np.array(im);assert np.array_equal(actual[:,:,3],want[:,:,3]);mask=want[:,:,3]>0;err=np.abs(actual[:,:,:3].astype(int)-want[:,:,:3].astype(int))[mask];assert err.max()<=9
  checks.append({'frame':i,'alpha_exact_original_nearest':True,'offset_name_size_preserved':True,'maximum_rgb565_error':int(err.max())})
 save('derivative-tests.json',{'path':str(dest),'sha256':sha(dest),'targets':list(range(21)),'non_target_frames':[],'checks':checks,'status':'trial-only awaiting visual review','source_current_unchanged':sha(SOURCE)==report['inputs']['source']['sha256'] and sha(CURRENT)==report['inputs']['current']['sha256']})
 print(dest)

# Separate finalization keeps the full generated trial as evidence and selects only
# visually improved normal-state book/chest art; remaining payloads stay exact.
def finalize_review():
 report=json.loads((OUT/'review-metrics.json').read_text(encoding='utf-8'));assert all(sha(Path(v['path']))==v['sha256'] for v in report['inputs'].values()),'Review inputs changed';cp,cf=read_spr(CURRENT);gp,gf=read_spr(OUT/'Buttons-qwen-trial.spr');sp,sf=read_spr(SOURCE)
 targets={3,6};payloads=[gf[i]['data'] if i in targets else f['data'] for i,f in enumerate(cf)]
 raw=bytearray(CURRENT.read_bytes()[:24]);pos=0
 for block in payloads:raw.extend(struct.pack('<I',pos));pos+=len(block)
 for block in payloads:raw.extend(block)
 struct.pack_into('<I',raw,4,len(raw));dest=OUT/'Buttons-readable-book-chest.spr';dest.write_bytes(raw);dp,df=read_spr(dest)
 checks=[]
 for i,(old,new) in enumerate(zip(cf,df)):
  assert (old['width'],old['height'],old['name'],old['offset'],old['flags'])==(new['width'],new['height'],new['name'],new['offset'],new['flags'])
  assert np.array_equal(np.array(decode(dp,new).getchannel('A')),np.array(decode(cp,old).getchannel('A')))
  if i not in targets:assert new['data']==old['data']
  checks.append({'frame':i,'metadata_exact':True,'alpha_exact':True,'non_target_payload_byte_identical':i not in targets})
 originals=[decode(sp,f) for f in sf];current=[decode(cp,f) for f in cf];generated=[decode(gp,f) for f in gf];adopted=[decode(dp,f) for f in df]
 sheet('adoptable-masked-hd.png',adopted)
 comp=Image.new('RGB',(1620,924))
 for x,name in enumerate(('original-lanczos-hd.png','current-hd.png','generated-masked-hd.png')):comp.paste(Image.open(OUT/name),(x*540,0))
 comp.save(OUT/'comparison-lanczos-current-generated-hd.png')
 # Full Portmanteau page sprite inventory (234 frames), no clipped first-21-only sheet.
 p,f=read_spr(RUNTIME/'Sprites/port-icons.spr');ims=[decode(p,x) for x in f];canvas=Image.new('RGB',(8*120,((len(f)+7)//8)*110),'#303038');d=ImageDraw.Draw(canvas)
 for i,im in enumerate(ims):
  x=i%8*120;y=i//8*110;canvas.paste(flatten(im),(x+(120-im.width)//2,y+20));d.text((x+4,y+3),str(i),fill='white')
 canvas.save(OUT/'port-page-sheet.png')
 # Source/current page variants are distinct collections; record frame identities,
 # rather than equating page-specific item buttons with shared toolbar frames.
 variants=[]
 for rel in ('Sprites/port-icons.spr','Interface/Grimoire/800x600/icons.spr','Interface/Grimoire/Generic/Icons.spr'):
  path=RUNTIME/rel;p,f=read_spr(path);original=ROOT/'modernization/assets/hd/source-original'/rel
  variants.append({'path':str(path),'sha256':sha(path),'frame_count':len(f),'source_original_path':str(original) if original.exists() else None,'source_original_sha256':sha(original) if original.exists() else None,'relationship':'separate page-specific sprite collection, not a 21-frame Buttons replacement'})
 verdict={'decision':'Selective readable book/chest derivative provided for main UI cases; reject full-sheet adoption','adoptable_derivative':str(dest),'sha256':sha(dest),'target_frames':sorted(targets),'non_target_frames':[i for i in range(21) if i not in targets],'runtime_acceptance':'pending user testing; no game launched','visual_findings':[
 'Nearest enlargement has visibly stepped page edges and character faces. Lanczos smooths edges without changing source alpha. Current preserves all 21 exact nearest-source silhouettes; it combines plain normal frames 0,3,9 with sharpened/redrawn other frames.',
 'Generated normal book 3 has clearly separated cover, page planes, green emblem and clasp at 94x82. Generated normal chest 6 has a clearer lid, interior compartments, hinge and bronze/gold metal planes at 94x82. These are useful readable redesigns, not rejected merely for departing from original shading.',
 'Generated faces are individually more readable but reinterpret expressions and introduce background or neck fragments inside the locked original mask. Full-sheet frames 2,8,14,17,20 show visible edge clipping because generated content did not exactly follow the state-specific silhouette.',
 'Raw generated three-state rows largely lost the original white pressed glint and normal/highlighted differences. Preserve existing highlighted and pressed payloads in the selective derivative; the change of art across states still requires main UI tests and user acceptance.',
 'All generation crops are fixed reference coordinates, with no invented position corrections. The original nearest alpha is restored after extraction; exact alpha alone does not prove the generated painted object follows its silhouette.',
 'Port-icons (234 frames) and Grimoire page icon collections have different counts and content; they are not alternate 21-frame toolbar replacements. They remain untouched. No runtime page transition or interaction claim is made.'
 ],'page_variants':variants,'checks':checks,'source_current_unchanged':all(sha(Path(v['path']))==v['sha256'] for v in report['inputs'].values()),'generation_count':1,'owned_job_id':json.loads((OUT/'qwen-call.json').read_text(encoding='utf-8'))['manager_job_id']}
 assert verdict['source_current_unchanged'];save('decision.json',verdict)
 (OUT/'REVIEW.md').write_text('# Bounded Portmanteau icon ART review\n\nDecision: selectively retain generated normal book (3) and chest (6) as a sidecar SPR candidate for main UI cases. Do not adopt the full generated sheet.\n\n'+ '\n\n'.join(verdict['visual_findings'])+'\n\nTests: 21-frame count, dimensions, offsets, names, flags and alpha exact; 19 non-target frame payloads byte-identical. Full trial RGB565 error <=9. Source/current/page variant input hashes unchanged. Runtime acceptance pending user testing.\n\nSource / nearest / Lanczos / current / generated images and per-frame exports are in this folder. Request, seed, status, owned job ID, observations and output hash are in qwen-call.json and qwen-status.json. No model substitution, game launch, installation or outside-scope write.\n',encoding='utf-8')
 print(json.dumps({'derivative':str(dest),'targets':sorted(targets),'checks':len(checks),'unchanged':verdict['source_current_unchanged']}))

def build_states():
 report=json.loads((OUT/'review-metrics.json').read_text(encoding='utf-8'))
 assert all(sha(Path(v['path']))==v['sha256'] for v in report['inputs'].values()),'Review inputs changed'
 cp,cf=read_spr(CURRENT);sp,sf=read_spr(SOURCE);gp,gf=read_spr(OUT/'Buttons-readable-book-chest.spr')
 targets=set(range(3,9));payloads=[f['data'] for f in cf];wanted={};rows=[]
 for normal in (3,6):
  frames=[cf[i] for i in range(normal,normal+3)]
  origin=[min(f['offset'][a] for f in frames) for a in (0,1)]
  size=[max(f['offset'][a]+f['width' if a==0 else 'height'] for f in frames)-origin[a] for a in (0,1)]
  def atlas(im,f):
   canvas=Image.new('RGBA',tuple(size));canvas.paste(im,tuple(f['offset'][a]-origin[a] for a in (0,1)));return np.array(canvas).astype(np.int16)
  old_normal=atlas(decode(cp,cf[normal]),cf[normal]);new_normal=atlas(decode(gp,gf[normal]),cf[normal])
  for i in range(normal,normal+3):
   f=cf[i];old_state=atlas(decode(cp,f),f);common=(old_state[:,:,3]>0)&(old_normal[:,:,3]>0)&(new_normal[:,:,3]>0)
   delta=old_state[:,:,:3]-old_normal[:,:,:3]
   composed=old_state.copy();composed[:,:,:3][common]=np.clip(new_normal[:,:,:3][common]+delta[common],0,255)
   x,y=[f['offset'][a]-origin[a] for a in (0,1)];crop=composed[y:y+f['height'],x:x+f['width']].astype(np.uint8)
   exact=np.array(decode(sp,sf[i]).getchannel('A').resize((f['width'],f['height']),Image.Resampling.NEAREST));crop[:,:,3]=exact
   im=Image.fromarray(crop);wanted[i]=im;im.save(OUT/f'states-frame-{i:02d}.png')
   block=bytearray(encode(f,im));struct.pack_into('<2i',block,12,*f['offset']);payloads[i]=bytes(block)
   posdelta=delta.mean(axis=2);flash=common&(posdelta>=25);outgain=(composed[:,:,:3]-new_normal[:,:,:3]).mean(axis=2)
   rows.append({'frame':i,'normal':normal,'atlas_origin':origin,'atlas_size':size,'atlas_position':[x,y],'dimensions':[f['width'],f['height']],'offset':f['offset'],'normal_rgb_coverage_missing_pixels':int(np.count_nonzero((old_state[:,:,3]>0)&~common)),'uncovered_policy':'original current state RGB retained only where no opaque generated normal covers atlas coordinate; no invented fill','positive_flash_pixels_delta_ge25':int(flash.sum()),'mean_transferred_flash_gain':float(outgain[flash].mean()) if flash.any() else 0,'mean_original_flash_gain':float(posdelta[flash].mean()) if flash.any() else 0,'method':'signed per-channel current-state minus current-normal RGB delta added to generated normal at identical atlas coordinate; clamp 0..255; exact nearest original alpha'})
 raw=bytearray(CURRENT.read_bytes()[:24]);position=0
 for block in payloads:raw.extend(struct.pack('<I',position));position+=len(block)
 for block in payloads:raw.extend(block)
 struct.pack_into('<I',raw,4,len(raw));dest=OUT/'Buttons-readable-book-chest-states.spr';dest.write_bytes(raw)
 dp,df=read_spr(dest);assert len(df)==21;checks=[]
 for i,(old,new) in enumerate(zip(cf,df)):
  assert all(old[k]==new[k] for k in ('width','height','offset','name','flags'))
  actual=np.array(decode(dp,new));assert np.array_equal(actual[:,:,3],np.array(decode(cp,old).getchannel('A')))
  if i not in targets:assert old['data']==new['data']
  else:
   expected=np.array(wanted[i]);mask=expected[:,:,3]>0;err=np.abs(actual[:,:,:3].astype(int)-expected[:,:,:3].astype(int))[mask];assert err.max()<=9
  checks.append({'frame':i,'metadata_alpha_exact':True,'non_target_payload_exact':i not in targets,'rgb565_error_max':int(err.max()) if i in targets else 0})
 # Pair current and candidate at the actual existing 2x source dimensions.
 canvas=Image.new('RGB',(4*180,4*132+28),'#303038');d=ImageDraw.Draw(canvas)
 for group,normal in enumerate((3,6)):
  for version,frames,pal in ((0,cf,cp),(1,df,dp)):
   y=(group*2+version)*132+28;d.text((5,y+45),('book' if normal==3 else 'chest')+' '+('current' if version==0 else 'candidate'),fill='white')
   for state in range(3):
    i=normal+state;f=frames[i];im=decode(pal,f);x=(state+1)*180
    d.text((x+12,y+2),str(i)+' '+('normal','hover','pressed')[state],fill='white')
    canvas.paste(flatten(im),(x+35+f['offset'][0],y+28+f['offset'][1]))
 canvas.save(OUT/'book-chest-states-current-candidate-2x.png')
 result={'derivative':str(dest),'sha256':sha(dest),'target_frames':sorted(targets),'non_target_count':15,'alignment_convention':'same as existing spr_sequence atlas: frame top-left = offset minus family minimum offset; no resize or recenter between states','state_derivation':rows,'tests':checks,'runtime_acceptance':'pending; no games launched','generated_normal_input_sha256':sha(OUT/'Buttons-readable-book-chest.spr'),'input_current_sha256':sha(CURRENT),'source_input_sha256':sha(SOURCE),'generation_calls_this_revision':0,'visual_decision':'UNSUITABLE FOR ADOPTION: pressed geometry creates incoherent rim/page edge overlays','visibly_preserved_pressflash':True,'alignment_confirmed':'All six frames use their unchanged offsets in a common family atlas, following existing spr_sequence convention. Native runtime placement was not tested. No frame resizing/recentering.','visual_findings':['Normal and hover use the same generated book/chest designs. Hover is visibly brighter.','Pressed book and chest visibly retain the original bright flash after signed RGB delta transfer.','Exact offset alignment exposes 412 book and 516 chest pressed opaque pixels without opaque generated-normal coverage. These retain current state RGB for diagnostic completeness; they are not claimed to be generated-base art.','Pressed chest has doubled upper rim/lid lines and inconsistent lower rim highlights; pressed book has conflicting page-edge texture. These are geometric overlay failures, not rejection of readable art.','The six-state derivative must not be adopted. Exact metadata and alpha tests pass, but do not establish coherent artwork.'], 'report_scope':'diagnostic only; main UI module builds independently' }
 save('book-chest-states-decision.json',result);print(json.dumps(rows))

if __name__=='__main__':
 if (Path(__file__).resolve().parents[2]/'modernization/assets/hd/seedvr2-ui-1.1/plan.json').exists():
  raise RuntimeError('Prior generation/review retired by user; use seedvr_ui_11.py and the SeedVR2 production root')

 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','generate','extract','finalize','states']);a=p.parse_args();({'finalize':finalize_review,'states':build_states}.get(a.mode) or globals()[a.mode])()
