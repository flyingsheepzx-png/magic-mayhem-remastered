"""Refresh the reviewed public-file manifest from tracked source files.

This records changes; it does not assert new source provenance or approve a
publication. Review Git diffs and run check_publication.py before publishing.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
manifest = ROOT/'source-distribution.json'
data = json.loads(manifest.read_text(encoding='utf-8'))
previous = {item['path']: item for item in data['files']}
names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
records = []
for name in sorted(filter(None, names)):
    if name == 'source-distribution.json':
        continue
    path = ROOT/name
    content = path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    item = dict(previous.get(name, {'path': name, 'role': 'public-development-entry'}))
    item.update(bytes=len(content), sha256=sha)
    records.append(item)
data['files'] = records
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Recorded',len(records),'reviewed public files (manifest excludes itself).')
