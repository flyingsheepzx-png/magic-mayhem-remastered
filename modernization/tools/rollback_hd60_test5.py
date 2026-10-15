"""Hash-gated rollback of the test5 UI layout correction in the HD lab."""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=(Path(__file__).resolve().parents[2] / "game")
BACKUP=ROOT/'modernization/backups/hd60-pre-test5-layout'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    rows=json.loads((BACKUP/'manifest.json').read_text())['files']
    for r in rows:
        target=(ROOT/r['path']).resolve()
        source=(BACKUP/r['backup']).resolve()
        if not target.is_relative_to(ROOT) or not source.is_relative_to(BACKUP):
            raise RuntimeError('Invalid manifest path')
        if sha(target)!=r['after_sha256'] or sha(source)!=r['before_sha256']:
            raise RuntimeError('Unknown live or backup bytes: '+r['path'])
    if not args.check:
        for r in rows: shutil.copy2(BACKUP/r['backup'],ROOT/r['path'])
    print(json.dumps({'ready':True,'mode':'check' if args.check else 'rollback','files':len(rows)}))
if __name__=='__main__': main()
