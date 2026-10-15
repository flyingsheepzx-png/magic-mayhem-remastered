"""Restore pre-layout release to a new folder; never overwrite current user state."""
from pathlib import Path
import json,hashlib,sys
C=Path(__file__).resolve().parent;B=C.parent
if len(sys.argv)!=2:raise SystemExit('Usage: python restore_release.py NEW_EMPTY_DIRECTORY')
d=Path(sys.argv[1]).resolve()
if d.exists():raise SystemExit('Destination must not exist. Preserve Save/settings before switching versions.')
m=json.loads((C/'manifest.json').read_text());d.mkdir(parents=True)
for row in m['files']:
 p=(d/row['path']).resolve();assert p.is_relative_to(d)
 raw=(B/'objects'/row['sha256'][:2]/row['sha256']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in m.get('directories',[]):
 p=(d/name).resolve();assert p.is_relative_to(d);p.mkdir(parents=True,exist_ok=True)
print('Restored previous release',len(m['files']),'files to',d)
