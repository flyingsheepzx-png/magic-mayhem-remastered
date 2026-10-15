"""Copy the approved SeedVR2 page icon derivative; never regenerate retired Qwen art."""
from pathlib import Path
import hashlib,json,struct,argparse
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'modernization/assets/hd/source-original/Sprites/SplIcons.spr'
EXPECTED='c4c47ba065669878afdc197558e3ad8a71d86bf4e0cfceda2f7d016e41b50e29'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(destination):
 production=ROOT/'modernization/assets/hd/seedvr2-ui-1.1/plan.json'
 if production.exists():
  plan=json.loads(production.read_text(encoding='utf-8'));row=next(a for a in plan['assets'] if a['path']=='Sprites/port-icons.spr')
  if row['status'] not in ('built','installed'):raise RuntimeError('Approved SeedVR2 icons are not ready; Qwen family retired')
  source=Path(row['output'])
  if sha(source)!=row['sha256']:raise RuntimeError('SeedVR2 page icon hash mismatch')
  destination.parent.mkdir(parents=True,exist_ok=True)
  destination.write_bytes(source.read_bytes());destination.with_suffix('.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');print(row['verification']);return
 raise RuntimeError('Qwen spell icon generation retired; use seedvr_ui_11.py')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'modernization/build/seedvr-ui-icons/port-icons.spr');build(p.parse_args().output)
