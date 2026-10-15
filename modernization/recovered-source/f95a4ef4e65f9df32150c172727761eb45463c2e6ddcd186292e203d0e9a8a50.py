"""Restore full pre-migration runtime to a new destination, never a live tree."""
from pathlib import Path
import json,hashlib,sys
K=Path(__file__).resolve().parent;B=K.parent
if len(sys.argv)!=3:raise SystemExit('Usage: python restore_runtime.py official|game|wide|mixed NEW_DIRECTORY')
name=sys.argv[1]
if name not in ('official','game','wide','mixed'):raise SystemExit('Unknown runtime')
d=Path(sys.argv[2]).resolve()
if d.exists():raise SystemExit('Destination must not exist; preserve new Save/settings separately')
m=json.loads((K/(name+'.json')).read_text());d.mkdir(parents=True)
for row in m['files']:
 p=(d/row['path']).resolve();assert p.is_relative_to(d);raw=(B/'objects'/row['sha256'][:2]/row['sha256']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for rel in m['directories']:
 p=(d/rel).resolve();assert p.is_relative_to(d);p.mkdir(parents=True,exist_ok=True)
print('Restored previous',name,'runtime to',d,';',len(m['files']),'files')
