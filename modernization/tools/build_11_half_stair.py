"""Hash-gated terrain stair delta; preserve all current embedded modules/HUD."""
from pathlib import Path
import argparse,json,shutil,subprocess,hashlib
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from build_11_fmv_h264 import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-half-stair'
BACK=b.ROOT/'modernization/backups/remastered-1.1-half-stair'
OLD='3791b8eabf83428b43c21d95d44d43996fd1f2275fbd1b882c803c4fa456ad41'

def build():
 OUT.mkdir(exist_ok=False);source=b.ROOT/'modernization/build/remastered-1.1-minimap-release'
 current=resources(base.DEST/base.ENTRY);assert resources(source/'candidate.exe')==current
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/terrain_diagonal.dll')==OLD
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 b.write(OUT/'before.json',rows)
 for number,name in [(101,'repath.dll'),(102,'qol_bindings.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[number])
 for name in ['candidate.rc','release.rc','remastered.ico']:shutil.copy2(source/name,OUT/name)
 shutil.copy2(b.ROOT/'modernization/runtime/terrain_diagonal/terrain_diagonal.cpp',OUT/'terrain_diagonal.cpp')
 (OUT/'terrain.cmd').write_text('@echo off\ncall "'+str(b.VC)+'" x86 >nul\nif errorlevel 1 exit /b 1\ncl /nologo /LD /O2 /EHsc /W4 terrain_diagonal.cpp /link /OUT:terrain_diagonal.dll /MAP:terrain.map\n')
 subprocess.run(['cmd','/c','terrain.cmd'],cwd=OUT,check=True)
 for name in ['launcher.cpp','release_launcher.cpp']:
  s=(source/name).read_text();assert s.count(OLD)==1;(OUT/name).write_text(s.replace(OLD,b.sha(OUT/'terrain_diagonal.dll')))
 command=(source/'build.cmd').read_text();command=command[command.index('rc /nologo'):]
 (OUT/'entries.cmd').write_text('@echo off\ncall "'+str(b.VC)+'" x86 >nul\nif errorlevel 1 exit /b 1\n'+command)
 subprocess.run(['cmd','/c','entries.cmd'],cwd=OUT,check=True)
 for name in ['candidate.exe','release.exe']:assert resources(OUT/name)==current

def install():
 base.idle();v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed' and v['save13_runtime_verified']
 assert b.sha(OUT/'terrain_diagonal.dll')==v['terrain_sha256'];changes=[]
 for i,r in enumerate(json.loads((OUT/'before.json').read_text())):
  e,m=Path(r['entry']),Path(r['manifest']);assert b.sha(e)==r['entry_sha256'] and b.sha(m)==r['manifest_sha256']
  assert b.sha(e.parent/'runtime/terrain_diagonal.dll')==OLD
  new=OUT/('candidate.exe' if r['kind']=='candidate' else 'release.exe');assert resources(new)==resources(e)
  manifest=json.loads(m.read_text(encoding='utf-8'));manifest['launcher_sha256']=b.sha(new);prefix='' if r['kind']=='candidate' else 'runtime/'
  manifest['files'][prefix+'terrain_diagonal.dll']=v['terrain_sha256'];manifest['half_stair_fix']=v
  if r['kind']=='release':manifest['files'][e.name]=b.sha(new)
  for j,(p,data) in enumerate([(e,new.read_bytes()),(e.parent/'runtime/terrain_diagonal.dll',(OUT/'terrain_diagonal.dll').read_bytes()),(m,(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())]):
   changes.append(dict(path=str(p),backup=str(BACK/f'{i}-{j}.bak'),before_sha256=b.sha(p),after_sha256=hashlib.sha256(data).hexdigest(),data=data))
 BACK.mkdir(exist_ok=False)
 for row in changes:Path(row['backup']).write_bytes(Path(row['path']).read_bytes())
 b.write(BACK/'rollback.json',[{k:v for k,v in row.items() if k!='data'} for row in changes])
 try:
  for row in changes:replace(Path(row['path']),row['data']);assert b.sha(Path(row['path']))==row['after_sha256']
 except BaseException:
  for row in reversed(changes):replace(Path(row['path']),Path(row['backup']).read_bytes())
  raise
 print('Installed half-stair fix; player acceptance pending')

def rollback():
 base.idle();rows=json.loads((BACK/'rollback.json').read_text())
 for r in rows:assert b.sha(Path(r['path']))==r['after_sha256'] and b.sha(Path(r['backup']))==r['before_sha256']
 for r in reversed(rows):replace(Path(r['path']),Path(r['backup']).read_bytes())

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
