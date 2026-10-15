"""Install/rollback the 1.1 PNG engine allowlist correction, no gameplay run."""
from pathlib import Path
import json,os,argparse
import build_remastered_11 as b
FIX=b.ROOT/'modernization/build/remastered-1.1-loader-fix'
BACK=b.ROOT/'modernization/backups/remastered-1.1-loader-fix'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
DLL=b.TARGET/'runtime/png_assets.dll'
MANIFEST=b.TARGET/'manifest.json'
def idle():
 from verify_hd60_runtime import configured_kernel,processes
 if any(n.startswith('chaos') for _,_,n in processes(configured_kernel())):raise RuntimeError('Close the game before installation')
def replace(path,data):
 temp=path.with_name(path.name+'.loader-fix.tmp')
 if temp.exists():raise RuntimeError('Unresolved file '+str(temp))
 temp.write_bytes(data);os.replace(temp,path)
def install():
 idle();b.verify()
 if BACK.exists():raise RuntimeError('Backup already exists; keep it')
 originals={ENTRY:ENTRY.read_bytes(),DLL:DLL.read_bytes(),MANIFEST:MANIFEST.read_bytes()};before=b.inventory(b.TARGET/'runtime')
 assert b.sha(DLL)=='206c645ec6f3e76bf548dedd9cc874f101dba1fc37d328f71343d8a3d4fa8839'
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 BACK.mkdir(parents=True)
 for p,data in originals.items():(BACK/p.name).write_bytes(data)
 m=json.loads(originals[MANIFEST]);m['files']['png_assets.dll']=b.sha(FIX/'png_assets.dll');m['launcher_sha256']=b.sha(FIX/ENTRY.name)
 m['png_loader_engine_fix']=dict(engine_sha256=m['engine_sha256'],module_sha256=m['files']['png_assets.dll'],backup=str(BACK),acceptance='pending user startup/gameplay testing')
 try:
  replace(DLL,(FIX/'png_assets.dll').read_bytes());replace(ENTRY,(FIX/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
  after=b.inventory(b.TARGET/'runtime');assert set(after)==set(before);assert [n for n in before if before[n]!=after[n]]==['png_assets.dll'];b.verify()
 except BaseException:
  for p,data in originals.items():replace(p,data)
  raise
 b.write(BACK/'installation.json',dict(module_sha256=b.sha(DLL),launcher_sha256=b.sha(ENTRY),before_module_sha256=b.sha(BACK/'png_assets.dll'),before_launcher_sha256=b.sha(BACK/ENTRY.name),changed_runtime_files=['png_assets.dll'],game_launched=False,fullreadable_map_preserved=True))
 print('Installed corrected PNG loader and synchronized launcher; Full Readable retained.')
def rollback():
 idle();b.verify();state=json.loads((BACK/'installation.json').read_text(encoding='utf-8'));assert b.sha(DLL)==state['module_sha256'] and b.sha(ENTRY)==state['launcher_sha256']
 m=json.loads(MANIFEST.read_text(encoding='utf-8'));m['files']['png_assets.dll']=state['before_module_sha256'];m['launcher_sha256']=state['before_launcher_sha256'];m.pop('png_loader_engine_fix',None)
 replace(DLL,(BACK/'png_assets.dll').read_bytes());replace(ENTRY,(BACK/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));b.verify();print('Previous loader/launcher restored (known startup defect also restored).')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);globals()[p.parse_args().action]()
