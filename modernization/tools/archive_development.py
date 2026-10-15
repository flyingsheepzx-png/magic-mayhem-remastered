"""Archive superseded large artifacts only after hash-verified checkpointing."""
from pathlib import Path
import json,os,hashlib,shutil,time,concurrent.futures,sys
ROOT=Path(__file__).resolve().parents[2];BACK=ROOT/'modernization/backups/development-20260930-remastered-1.0';OUT=ROOT/'modernization/releases/remastered-1.0'
def h(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):d.update(x)
 return d.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory(root):
 total=0;files=0;groups={}
 for base,dirs,names in os.walk(root,followlinks=False):
  p=Path(base);dirs[:]=[x for x in dirs if x!='.git' and not (p/x).is_junction() and not (p/x).is_symlink()]
  for n in names:
   f=p/n;s=f.stat().st_size;files+=1;total+=s
   rel=f.relative_to(root);key='/'.join(rel.parts[:2]) if rel.parts[0]=='modernization' and len(rel.parts)>1 else rel.parts[0]
   groups[key]=groups.get(key,0)+s
 return {'files':files,'bytes':total,'groups':groups}
def prepare():
 assert json.loads((BACK/'result.json').read_text())['phase']=='verified'
 controls=json.loads((BACK/'control-hashes.json').read_text());assert h(BACK/'manifest.json')==controls['manifest.json']
 state=json.loads((ROOT/'modernization/wide169-installed.json').read_text());active=Path(state['package']).resolve();assert active.is_relative_to(ROOT)
 dirs=[]
 for p in (ROOT/'modernization/build/wide169').iterdir():
  if p.is_dir() and p.name.startswith('package-') and p.resolve()!=active:dirs.append(p)
 for p in (ROOT/'modernization/playtests').iterdir():
  if p.is_dir() and p.name!='mixed-ui-v4':dirs.append(p)
 for name in ['baseline-comparisons','native-ui-2k-probe','preview-wide169-v7-qwen','loading-frames','qwen-value-audits','keyed-pages','stale-page-fix','battle-sharpen-trial','launcher-mixed-fix','grimoire-tab-state','ss','normal-mouse-probe','cursor-progress-verification','background-trials','cursor-loading-probe','realm-draw-probes']:
  p=ROOT/'modernization/assets/hd'/name
  if p.is_dir():dirs.append(p)
 selected=[]
 for folder in dirs:
  assert folder.resolve().is_relative_to(ROOT) and not folder.is_junction() and not folder.is_symlink()
  for base,ds,fs in os.walk(folder,followlinks=False):
   p=Path(base)
   assert not any((p/n).is_junction() or (p/n).is_symlink() or n=='.git' for n in ds),'Nested link/repository'
   selected.extend(p/n for n in fs)
 logs=ROOT/'modernization/logs';loose=[]
 for base,ds,fs in os.walk(logs,followlinks=False):
  p=Path(base);ds[:]=[n for n in ds if not (p/n).is_junction() and not (p/n).is_symlink()]
  for n in fs:
   f=p/n
   if f.suffix.lower() in ('.png','.bmp','.jpg','.jpeg','.avi','.csv','.dll','.sav','.raw','.bin') or f.stat().st_size>10*1024*1024:loose.append(f)
 selected.extend(loose)
 prior=json.loads((BACK/'manifest.json').read_text());rows={x['path']:x for x in prior['files']};supp=BACK/'supplemental-manifest.json'
 if supp.exists():rows.update({x['path']:x for x in json.loads(supp.read_text())['files']})
 before=inventory(ROOT);write(OUT/'aggressive-cleanup-before.json',before)
 records=[];new=[];last=time.time();checked=set()
 def inspect(f):
  st=f.stat();sha=h(f);st2=f.stat();assert (st.st_size,st.st_mtime_ns)==(st2.st_size,st2.st_mtime_ns),str(f)
  return f,sha,st2
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  pending=set();it=iter(selected);done=False
  while pending or not done:
   while len(pending)<64 and not done:
    try:pending.add(pool.submit(inspect,next(it)))
    except StopIteration:done=True
   completed,pending=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
   for fut in completed:
    f,sha,st=fut.result();rel=f.relative_to(ROOT).as_posix();obj=BACK/'objects'/sha[:2]/sha
    if not obj.exists():obj.parent.mkdir(exist_ok=True);shutil.copy2(f,obj)
    if sha not in checked:assert h(obj)==sha and obj.stat().st_size==st.st_size;checked.add(sha)
    row={'path':rel,'sha256':sha,'size':st.st_size,'mtime_ns':st.st_mtime_ns}
    if rel not in rows or rows[rel]['sha256']!=sha:new.append(row)
    records.append(row)
   if time.time()-last>20:print(json.dumps({'phase':'verify-archive','files':len(records),'bytes':sum(x['size'] for x in records)}),flush=True);last=time.time()
 archive={'directories':[p.relative_to(ROOT).as_posix() for p in dirs],'loose_files':[p.relative_to(ROOT).as_posix() for p in loose],'files':records,'new_or_changed_files':new,'bytes':sum(x['size'] for x in records),'active_package_retained':str(active),'latest_hd_playtest_retained':'modernization/playtests/mixed-ui-v4'}
 write(BACK/'aggressive-archive.json',archive);write(OUT/'aggressive-cleanup-plan.json',{k:v for k,v in archive.items() if k not in ('files','new_or_changed_files')})
 print(json.dumps({'directories':len(dirs),'files':len(records),'bytes':archive['bytes'],'new_or_changed_files':len(new)},indent=2),flush=True)
if __name__=='__main__':prepare()
