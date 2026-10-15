from pathlib import Path
import json,hashlib,sys,os,shutil,subprocess
b=Path(__file__).resolve().parent
if len(sys.argv)!=2:raise SystemExit('Usage: python restore.py NEW_DESTINATION')
d=Path(sys.argv[1]).resolve()
if d.exists():raise SystemExit('Destination must not exist; live trees are never overwritten')
m=json.loads((b/'manifest.json').read_text(encoding='utf-8'));d.mkdir(parents=True)
supplement=b/'supplemental-manifest.json'
if supplement.exists():
 merged={row['path']:row for row in m['files']}
 for row in json.loads(supplement.read_text(encoding='utf-8'))['files']:merged[row['path']]=row
 m['files']=list(merged.values())
for name in m.get('directories',[]):
 rel=Path(name);target=(d/rel).resolve()
 if rel.is_absolute() or not target.is_relative_to(d):raise RuntimeError('Unsafe directory path')
 target.mkdir(parents=True,exist_ok=True)
for row in m['files']:
 rel=Path(row['path']);target=(d/rel).resolve()
 if rel.is_absolute() or not target.is_relative_to(d):raise RuntimeError('Unsafe manifest path')
 obj=b/'objects'/row['sha256'][:2]/row['sha256'];raw=obj.read_bytes()
 if len(raw)!=row['size'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('Corrupt object '+row['path'])
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);os.utime(target,ns=(row['mtime_ns'],row['mtime_ns']))
for row in m.get('junctions',[]):
 target=d/row['path'];referent=d/row['target_relative'];target.parent.mkdir(parents=True,exist_ok=True)
 os.symlink(referent,target,target_is_directory=True) if os.name!='nt' else subprocess.run(['powershell','-NoProfile','-Command','New-Item -ItemType Junction -Path $env:MM_RESTORE_JUNCTION -Target $env:MM_RESTORE_TARGET | Out-Null'],env=dict(os.environ,MM_RESTORE_JUNCTION=str(target),MM_RESTORE_TARGET=str(referent)),check=True)
print('Restored',len(m['files']),'files to',d)
