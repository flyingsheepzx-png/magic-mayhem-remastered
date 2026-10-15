"""Full hash-deduplicated checkpoint; no game control and no Git mutations."""
from pathlib import Path
import os,json,hashlib,shutil,subprocess,time,concurrent.futures,sys
ROOT=Path(__file__).resolve().parents[2]
BACK=ROOT/'modernization/backups/development-20260930-remastered-1.0'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)
def paths():
 for base,dirs,files in os.walk(ROOT,followlinks=False):
  p=Path(base)
  dirs[:]=[d for d in dirs if d!='.git' and (p/d)!=BACK and not (p/d).is_junction() and not (p/d).is_symlink()]
  for n in files:
   f=p/n
   if f.is_symlink():continue
   if n.lower().startswith('.env') or n.lower() in ('credentials.json','secrets.json','id_rsa','id_ed25519') or f.suffix.lower() in ('.pfx','.p12','.key'):
    raise RuntimeError('Credential-like path excluded; resolve backup scope: '+str(f.relative_to(ROOT)))
   yield f
RESTORE=r'''from pathlib import Path
import json,hashlib,sys,os,shutil,subprocess
b=Path(__file__).resolve().parent
if len(sys.argv)!=2:raise SystemExit('Usage: python restore.py NEW_DESTINATION')
d=Path(sys.argv[1]).resolve()
if d.exists():raise SystemExit('Destination must not exist; live trees are never overwritten')
m=json.loads((b/'manifest.json').read_text(encoding='utf-8'));d.mkdir(parents=True)
for row in m['files']:
 rel=Path(row['path']);target=(d/rel).resolve()
 if rel.is_absolute() or not target.is_relative_to(d):raise RuntimeError('Unsafe manifest path')
 obj=b/'objects'/row['sha256'][:2]/row['sha256'];raw=obj.read_bytes()
 if len(raw)!=row['size'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('Corrupt object '+row['path'])
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);os.utime(target,ns=(row['mtime_ns'],row['mtime_ns']))
for row in m.get('junctions',[]):
 target=d/row['path'];referent=d/row['target_relative'];target.parent.mkdir(parents=True,exist_ok=True)
 os.symlink(referent,target,target_is_directory=True) if os.name!='nt' else subprocess.run(['powershell','-NoProfile','-Command','New-Item -ItemType Junction -Path $args[0] -Target $args[1] | Out-Null',str(target),str(referent)],check=True)
print('Restored',len(m['files']),'files to',d)
'''
def snapshot():
 if BACK.exists():raise RuntimeError('Checkpoint already exists')
 BACK.mkdir(parents=True);(BACK/'objects').mkdir()
 (BACK/'restore.py').write_text(RESTORE,encoding='utf-8')
 (BACK/'status.txt').write_bytes(git('status','--porcelain=v1','--untracked-files=all'))
 (BACK/'working.patch').write_bytes(git('diff','--binary','--no-ext-diff'))
 (BACK/'staged.patch').write_bytes(git('diff','--cached','--binary','--no-ext-diff'))
 (BACK/'HEAD.txt').write_bytes(git('rev-parse','HEAD'))
 subprocess.run(['git','bundle','create',str(BACK/'repository.bundle'),'--all'],cwd=ROOT,check=True)
 index=ROOT/'.git/index'
 if index.exists():shutil.copy2(index,BACK/'git-index')
 rows=[];dirs=[];junctions=[];total=0;unique=0;started=time.time()
 for base,ds,fs in os.walk(ROOT,followlinks=False):
  p=Path(base)
  for n in ds:
   x=p/n
   if x==BACK or n=='.git':continue
   if x.is_junction():
    target=x.resolve();assert target.is_relative_to(ROOT)
    junctions.append({'path':x.relative_to(ROOT).as_posix(),'target_relative':target.relative_to(ROOT).as_posix()})
   elif not x.is_symlink():dirs.append(x.relative_to(ROOT).as_posix())
  ds[:]=[n for n in ds if n!='.git' and (p/n)!=BACK and not (p/n).is_junction() and not (p/n).is_symlink()]
 def inspect(f):
  before=f.stat();h=digest(f);after=f.stat()
  if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('File changed during backup: '+str(f))
  return f,h,after
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  pending=set();iterator=iter(paths());done=False;last=time.time()
  while pending or not done:
   while len(pending)<64 and not done:
    try:pending.add(pool.submit(inspect,next(iterator)))
    except StopIteration:done=True
   completed,pending=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
   for future in completed:
    f,h,st=future.result();obj=BACK/'objects'/h[:2]/h
    if not obj.exists():
     obj.parent.mkdir(exist_ok=True);shutil.copy2(f,obj)
     assert digest(obj)==h,'Source changed while copying: '+str(f)
     unique+=st.st_size
    rows.append({'path':f.relative_to(ROOT).as_posix(),'sha256':h,'size':st.st_size,'mtime_ns':st.st_mtime_ns});total+=st.st_size
   if time.time()-last>20:
    print(json.dumps({'phase':'snapshot','files':len(rows),'logical_GB':round(total/1e9,2),'unique_GB':round(unique/1e9,2)}),flush=True);last=time.time()
 write(BACK/'manifest.json',{'root':str(ROOT),'date':'2026-09-30','files':sorted(rows,key=lambda x:x['path']),'directories':sorted(dirs),'junctions':junctions})
 readme='开发环境完整备份（2026-09-30）\n\nmanifest.json 映射所有文件到 objects 中的 SHA-256 对象，相同内容只存一份。\n包含未提交、未跟踪、Git 忽略文件、存档、历史包和先前备份。\n恢复到一个不存在的新目录：\n  python restore.py "D:\\Games\\MagicMayham-Restored"\n运行恢复脚本需要 Python 3.12+，无需第三方库。不会覆盖现有目录。\n\nGit 历史恢复（在恢复目录内执行，勿对现有开发树执行）：\n  git init\n  git fetch "本备份目录\\repository.bundle" "+refs/heads/*:refs/heads/*"\n  git symbolic-ref HEAD refs/heads/restored-checkpoint\n  git update-ref HEAD '+git('rev-parse','HEAD').decode().strip()+'\n  git reset --mixed HEAD\n以上 reset 只重建新目录的索引，不改已恢复工作文件；原暂存差异保存于 staged.patch。\n也保存了 git-index、working.patch、status.txt 和 HEAD.txt。\n不要使用 reset --hard 或 clean。\n\ncleanup.json 记录整理时移除的临时文件，它们均可从本快照恢复。\nresult.json 记录对象校验结果。开发运行目录的 modernization 联接在新根目录中重建。\n'
 (BACK/'readme.txt').write_text(readme,encoding='utf-8')
 write(BACK/'result.json',{'phase':'snapshot_complete','files':len(rows),'logical_bytes':total,'unique_bytes':unique,'elapsed_seconds':round(time.time()-started,1)})
 print('Snapshot complete',len(rows),'files',flush=True)
def verify():
 m=json.loads((BACK/'manifest.json').read_text());objects={r['sha256']:r['size'] for r in m['files']}
 count=0;last=time.time()
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  def check(item):
   h,size=item;p=BACK/'objects'/h[:2]/h
   assert p.stat().st_size==size and digest(p)==h,h
  for _ in pool.map(check,objects.items(),chunksize=16):
   count+=1
   if time.time()-last>20:print('Verified objects',count,'/',len(objects),flush=True);last=time.time()
 subprocess.run(['git','bundle','verify',str(BACK/'repository.bundle')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 result=json.loads((BACK/'result.json').read_text());result.update(phase='verified',objects=count,manifest_sha256=digest(BACK/'manifest.json'));write(BACK/'result.json',result)
 print(json.dumps(result),flush=True)
def cleanup():
 result=json.loads((BACK/'result.json').read_text());assert result['phase']=='verified'
 m=json.loads((BACK/'manifest.json').read_text());rows={r['path']:r for r in m['files']};removed=[]
 for rel,row in rows.items():
  parts=Path(rel).parts
  eligible=('__pycache__' in parts or rel=='NUL.obj' or rel.startswith('modernization/releases/remastered-1.0/incomplete-stage/') or rel.startswith(('game-wide169/ss/','game-wide169/modernization/logs/')) or (rel.startswith('modernization/runtime/') and Path(rel).suffix.lower() in ('.obj','.exp','.lib')) or (rel.startswith('modernization/releases/remastered-1.0/') and Path(rel).suffix.lower() in ('.obj','.res')))
  if not eligible:continue
  f=ROOT/rel;assert f.resolve().is_relative_to(ROOT) and not f.is_symlink() and not f.is_junction()
  assert digest(f)==row['sha256'],'Changed since backup: '+rel
  f.unlink();removed.append({'path':rel,'sha256':row['sha256'],'size':row['size']})
 # Remove only now-empty cache directories, never runtime Save or evidence folders.
 dirs=[ROOT/d for d in m['directories'] if '__pycache__' in Path(d).parts or d.startswith('modernization/releases/remastered-1.0/incomplete-stage')]
 for d in sorted(dirs,key=lambda p:len(p.parts),reverse=True):
  assert d.resolve().is_relative_to(ROOT) and not d.is_symlink() and not d.is_junction()
  if d.exists() and not any(d.iterdir()):d.rmdir()
 write(BACK/'cleanup.json',{'removed':removed,'bytes':sum(r['size'] for r in removed)})
 print(json.dumps({'removed_files':len(removed),'freed_bytes':sum(r['size'] for r in removed)}))
if __name__=='__main__':{'snapshot':snapshot,'verify':verify,'cleanup':cleanup}[sys.argv[1]]()
