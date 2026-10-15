"""Audit all installed UI media against retained generation provenance, read-only."""
import json,collections,hashlib,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
RT=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime')
OUT=ROOT/'modernization/assets/hd/ui-coverage-20261002'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 OUT.mkdir(parents=True,exist_ok=True)
 plan=load(ROOT/'modernization/assets/hd/seedvr2-ui-1.1/plan.json');tasks={t['id']:t for t in plan['tasks']}
 known={};failures=[]
 for a in plan['assets']:
  ids=([a['task']] if a.get('task') else [])+[x['task'] for x in a.get('atlases',[])]
  complete=all(tasks[t]['status']=='complete' and tasks[t].get('job_id') and tasks[t].get('output_sha256') for t in ids)
  category='seedvr2' if ids and complete else ('procedural-resize' if not ids else 'incomplete-generation')
  if 'approved_source' in a:category='approved-qwen'
  known[a['path'].lower()]={'category':category,'expected':a['sha256'],'jobs':[tasks[t].get('job_id') for t in ids],'record':'seedvr2-ui-1.1/plan.json','source':a.get('source')}
 tutorial=load(ROOT/'modernization/build/remastered-1.1-campaign-ui/tutorial-jobs.json')
 for a in tutorial['jobs']:
  rel=Path(a['output']).relative_to(ROOT/'modernization/build/remastered-1.1-campaign-ui/runtime').as_posix()
  known[rel.lower()]={'category':'seedvr2','expected':a['sha256'],'jobs':[a['job_id']],'record':'campaign-ui/tutorial-jobs.json','source':a['source']}
 staged=load(ROOT/'modernization/build/remastered-1.1-campaign-ui/staged-assets.json')
 for a in staged['records']:
  if a.get('variant') and a.get('kind') in ['raster','sprite']:
   source=known.get(a.get('original_path','').lower())
   if source:known[a['path'].lower()]=dict(source,expected=a['sha256'],record='campaign-ui/staged-assets.json')
 for world in ['Medieval','Greek']:
  v=load(ROOT/f'modernization/assets/hd/fullreadable-realms-20261002/{world}/verification.json')
  for a in v['records']:known[a['path'].lower()]={'category':'approved-qwen' if '_Map' in a['path'] else 'derived-qwen-mask','expected':a['sha256'],'jobs':[],'record':'fullreadable-realms-20261002/'+world+'/verification.json'}
 # Celtic selected overlays are deterministic native-mask derivatives, not SR jobs.
 v=load(ROOT/'modernization/build/remastered-1.1-qwen-highlight/verification.json')
 for a in v['records']:
  if a['world']=='Celtic':known[a['path'].lower()]={'category':'derived-qwen-mask','expected':a['sha256'],'jobs':[],'record':'qwen-highlight/verification.json'}
 manifest=load(RT.parent/'release-manifest.json');hud=load(ROOT/'modernization/assets/hd/battle-hud-1.1/pack.json')
 for a in load(ROOT/'modernization/build/remastered-1.1-stat-preview/verification.json')['assets']:
  known[a['path'].lower()]={'category':'procedural-resize','expected':a['output_sha256'],'jobs':[],'record':'stat-preview/verification.json'}
 for a in load(ROOT/'modernization/build/remastered-1.1-portal-highlight/verification.json')['records']:
  if 'Celtic' in a['path']:known[a['path'].lower()]={'category':'derived-qwen-mask','expected':a['sha256'],'jobs':[],'record':'portal-highlight/verification.json'}
 # Book PNGs are lossless derivatives of already generated JPEG-page tasks.
 for stem,folder in [('ClosedBook','remastered-1.1-book-open'),('Backdrop','remastered-1.1-grimoire-load')]:
  rel='Interface/Grimoire/800x600/'+stem+'.PNG';old=known.get(rel[:-4].lower()+'.jpg')
  if old:
   candidates=list((ROOT/'modernization/build'/folder).rglob(stem+'.PNG'))
   matched=next((p for p in candidates if sha(p)==sha(RT/rel)),None)
   if matched:known[rel.lower()]=dict(old,expected=sha(matched),record=str(matched.relative_to(ROOT)))
 dialog=ROOT/'modernization/build/remastered-1.1-confirm-dialog/dialog.PNG'
 known['bitmaps/hd-ui/dlgback 800x600.png']={'category':'resize-only-confirmed','expected':sha(dialog),'jobs':[],'record':'build_11_confirm_dialog.py: original Lanczos2x, no model'}
 common=load(ROOT/'modernization/assets/hd/seedvr2-common-ui-1.1/plan.json')
 for a in common['records']:
  for item in [a]+([a['hd_variant']] if a.get('hd_variant') else []):
   known[item['path'].lower()]={'category':'seedvr2','expected':item['sha256'],'jobs':[a['job_id']],'record':'seedvr2-common-ui-1.1/plan.json','source':a['source']}
 assert sha(RT/'Sprites/battle-hud.bin')==hud['pack_sha256'],'HUD provenance mismatch'
 hud_names={a['name'].split(':')[0].lower() for a in hud['entries'] if a['kind'] in [1,3]}
 texts=[]
 for p in RT.rglob('*.cfg'):
  if 'encrypted' not in str(p).lower():texts.append((p.relative_to(RT).as_posix(),p.read_text(encoding='latin-1').lower()))
 rows=[];extensions={'.png','.jpg','.jpeg','.bmp','.pcx','.spr','.tga'}
 for top in ['Interface','Portraits','SpeechBox','Bitmaps','Sprites']:
  for p in sorted((RT/top).rglob('*')):
   if not p.is_file() or p.suffix.lower() not in extensions:continue
   rel=p.relative_to(RT).as_posix();digest=sha(p);record=known.get(rel.lower());category=record['category'] if record else 'unproven'
   if record and digest!=record['expected']:category='provenance-mismatch'
   if top=='Bitmaps' and p.name.lower() in hud_names:category='seedvr2-runtime-overlay'
   if rel.lower()=='sprites/splicons.spr':category='seedvr2-runtime-overlay'
   counterpart=p.with_suffix('.PNG');has_sibling=p.suffix.lower()!='.png' and counterpart.exists()
   refs=[n for n,t in texts if p.name.lower() in t or (p.stem.lower()+'.bmp') in t]
   row={'path':rel,'sha256':digest,'category':category,'manifest_match':manifest['files'].get('runtime/'+rel)==digest,'provenance':record,'png_sibling':counterpart.relative_to(RT).as_posix() if has_sibling else None,'legacy_640':'640x480' in rel.lower(),'cfg_references':refs}
   if p.suffix.lower()!='.spr':
    try:
     with Image.open(p) as im:row['size']=list(im.size);row['codec']=im.format
    except OSError as e:row['decode_error']=str(e)
   if category=='unproven':
    origdir=ROOT/'modernization/assets/hd/source-original'/p.relative_to(RT).parent
    original=next((q for q in origdir.glob('*') if q.stem.lower()==p.stem.lower() and q.suffix.lower() in extensions),None)
    if original:
     row['original_path']=str(original);row['original_sha256']=sha(original)
     if p.suffix.lower()=='.spr':row['original_exact']=sha(original)==digest
     else:
      try:
       with Image.open(original) as a,Image.open(p) as b:row['original_exact']=a.size==b.size and a.convert('RGB').tobytes()==b.convert('RGB').tobytes()
      except OSError:pass
   if category=='unproven':
    if has_sibling:row['triage']='legacy sibling; PNG loader resolution must be considered'
    elif row['legacy_640']:row['triage']='legacy resolution variant; runtime use not established'
    elif top=='Sprites' and re.match(r'(effects\d+|cure|subvert|flys|lordking|manablack|manadullyellow|manayellow)',p.stem,re.I):row['triage']='world effect/actor, outside UI artwork scope'
    elif '_border_' in p.name.lower() or 'silhouette' in p.name.lower():row['triage']='original semantic mask/portal source; retain'
    elif top in ['SpeechBox','Portraits'] and (RT/top/'hd-ui'/p.with_suffix('.PNG').name).exists():row['triage']='original counterpart with generated hd-ui override; retain'
    else:row['triage']='UI candidate: no matching SeedVR2 output evidence'
   if category=='resize-only-confirmed':row['triage']='UI artwork: confirmed ordinary resize without SeedVR2'
   if not row['manifest_match']:failures.append(rel)
   rows.append(row)
 summary=dict(collections.Counter(r['category'] for r in rows));gaps=[r for r in rows if r.get('triage','').startswith('UI candidate') or r['category'] in ['provenance-mismatch','resize-only-confirmed']]
 geometry=[]
 for r in rows:
  if r['path'].startswith('Interface/') and '/800x600/' in r['path'] and r.get('size')==[1280,720] and r['category']=='seedvr2':geometry.append(r['path'])
 report={'runtime':str(RT),'scope':'Every raster and SPR under Interface/Portraits/SpeechBox/Bitmaps/Sprites. Font files are separate native rendering; effects classified separately. CFG references are supporting evidence, not proof of runtime use. No SR claim from dimensions alone.','summary':summary,'files':rows,'ui_candidates':len(gaps),'manifest_mismatches':failures,'generated_but_low_resolution_pages':geometry}
 (OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Installed UI super-resolution coverage audit','',report['scope'],'',f'Total {len(rows)} media files; {len(gaps)} unresolved UI candidates.','', '| Category | Count |','|---|---:|']+[f'| {k} | {v} |' for k,v in summary.items()]
 lines+=['','## Unresolved / non-SeedVR UI candidates','','| Asset | Size | Evidence |','|---|---|---|']+[f"| {r['path']} | {r.get('size','SPR')} | {r.get('triage',r['category'])}; cfg references {len(r['cfg_references'])} |" for r in gaps]
 lines+=['','## Generated artwork still stored at old page resolution','']+[ '- '+p for p in geometry]
 lines+=['','## Deterministic UI graphics','', 'Thin statistic/progress bars should retain exact procedural geometry rather than hallucinated texture. Approved Qwen world maps and their masks are intentional exceptions. Original portrait/ spell sheets may remain unchanged while the verified battle-hud.bin supplies generated pixels during presentation.','', 'All individual classifications, source records, manager job IDs, installed hashes, original-pixel comparisons, legacy variants and manifest checks are in audit.json. Unproven resources are not asserted to be sharpening-only without historical generation evidence.']
 (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps({'total':len(rows),'summary':summary,'ui_candidates':len(gaps),'manifest_mismatches':len(failures)},indent=2))
if __name__=='__main__':run()
