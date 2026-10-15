"""Hash-verified isolated minimap layout fix with transactional rollback."""
import argparse,json,os
import pefile
import build_remastered_11 as b
FIX=b.ROOT/'modernization/build/remastered-1.1-minimap-v2'
BACK=b.ROOT/'modernization/backups/remastered-1.1-minimap-v2'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'
def idle():
 from verify_hd60_runtime import configured_kernel,processes
 if any(n.startswith('chaos') or n.startswith('magicmayhem') for _,_,n in processes(configured_kernel())):raise RuntimeError('Close game before replacing candidate')
def resources(path):
 pe=pefile.PE(str(path));result={}
 try:
  for row in pe.DIRECTORY_ENTRY_RESOURCE.entries:
   if row.id==10:
    for item in row.directory.entries:
     d=item.directory.entries[0].data.struct
     result[item.id]=pe.get_data(d.OffsetToData,d.Size)
 finally:pe.close()  # Release Windows mapped-file lock before launcher replacement.
 return result
def replace(path,data):
 temp=path.with_name(path.name+'.realm-fix.tmp')
 if temp.exists():raise RuntimeError('Unresolved temporary file '+str(temp))
 temp.write_bytes(data);os.replace(temp,path)
def install():
 idle();b.verify()
 if BACK.exists():raise RuntimeError('Keep existing backup; do not install twice')
 assert b.sha(ENTRY)=='a22d3f149abc98cdc3e8fb0667b3c431a2bac00a9cfef90556b0fdf729a2be74'
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 r=resources(ENTRY);new=resources(FIX/ENTRY.name)
 assert new[101]==r[101] and new[102]==(FIX/'qol_bindings.dll').read_bytes()
 assert json.loads((FIX/'minimap-verification.json').read_text(encoding='utf-8'))['qol_sha256']==b.sha(FIX/'qol_bindings.dll')
 before=b.inventory(b.TARGET/'runtime');originals={ENTRY:ENTRY.read_bytes(),MANIFEST:MANIFEST.read_bytes()}
 BACK.mkdir()
 for p,data in originals.items():(BACK/p.name).write_bytes(data)
 m=json.loads(originals[MANIFEST]);m['launcher_sha256']=b.sha(FIX/ENTRY.name)
 m['minimap_coordinate_fix']=dict(module_sha256=b.sha(FIX/'qol_bindings.dll'),backup=str(BACK),acceptance='offline passed; paired runtime comparison pending',engine_unchanged=True)
 try:
  replace(ENTRY,(FIX/ENTRY.name).read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
  assert b.inventory(b.TARGET/'runtime')==before;b.verify()
 except BaseException:
  for p,data in originals.items():replace(p,data)
  raise
 b.write(BACK/'installation.json',dict(launcher_sha256=b.sha(ENTRY),before_launcher_sha256=b.sha(BACK/ENTRY.name),module_sha256=b.sha(FIX/'qol_bindings.dll'),runtime_unchanged=True,resource101_unchanged=True,fullreadable_preserved=True))
 print('Installed isolated minimap layout fix:',ENTRY)
def rollback():
 idle();state=json.loads((BACK/'installation.json').read_text(encoding='utf-8'))
 assert b.sha(ENTRY)==state['launcher_sha256']
 assert b.sha(BACK/ENTRY.name)==state['before_launcher_sha256']
 replace(ENTRY,(BACK/ENTRY.name).read_bytes());replace(MANIFEST,(BACK/'manifest.json').read_bytes());b.verify()
 print('Restored preceding 1.1 candidate; saves untouched')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['install','rollback']);globals()[parser.parse_args().action]()
