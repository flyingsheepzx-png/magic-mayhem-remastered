"""Restore an archived project subtree without overwriting different files."""
from pathlib import Path
import json,hashlib,sys,os
BACK=Path(__file__).resolve().parent
if len(sys.argv) not in (2,3):raise SystemExit('Usage: python restore_selected.py PROJECT_RELATIVE_PREFIX [DESTINATION_ROOT]')
prefix=sys.argv[1].replace('\\','/').rstrip('/');rel=Path(prefix)
if not prefix or rel.is_absolute() or '..' in rel.parts:raise SystemExit('Use a safe project-relative prefix')
m=json.loads((BACK/'manifest.json').read_text(encoding='utf-8'));root=Path(sys.argv[2]).resolve() if len(sys.argv)==3 else Path(m['root']).resolve()
rows={r['path']:r for r in m['files']}
for name,key in [('supplemental-manifest.json','files'),('aggressive-archive.json','new_or_changed_files')]:
 p=BACK/name
 if p.exists():rows.update({r['path']:r for r in json.loads(p.read_text(encoding='utf-8')).get(key,[])})
selected=[r for n,r in rows.items() if n==prefix or n.startswith(prefix+'/')]
if not selected:raise SystemExit('No snapshot files match this prefix')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Validate every path/object and detect conflicts before writing anything.
for row in selected:
 path=root/row['path'];assert path.resolve().is_relative_to(root),row['path']
 assert not any(p.is_junction() or p.is_symlink() for p in [path,*path.parents] if p.is_relative_to(root)),'Linked destination'
 obj=BACK/'objects'/row['sha256'][:2]/row['sha256'];assert obj.stat().st_size==row['size'] and digest(obj)==row['sha256'],row['path']
 if path.exists() and digest(path)!=row['sha256']:raise SystemExit('Different existing file; restore to another root: '+str(path))
for row in selected:
 p=root/row['path']
 if p.exists():continue
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((BACK/'objects'/row['sha256'][:2]/row['sha256']).read_bytes());os.utime(p,ns=(row['mtime_ns'],row['mtime_ns']))
print('Restored/verified',len(selected),'files for',prefix,'under',root)
