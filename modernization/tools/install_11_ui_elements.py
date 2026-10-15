"""Transactional Portmanteau UI-only icons/tooltip module checkpoint."""
import argparse,json,hashlib
import build_remastered_11 as b
from install_11_realm_fix import idle,resources,replace
FIX=b.ROOT/'modernization/build/remastered-1.1-ui-elements'
BACK=b.ROOT/'modernization/backups/remastered-1.1-ui-elements'
ENTRY=b.TARGET/'MagicMayhem-Remastered-1.1.exe';MANIFEST=b.TARGET/'manifest.json'
REL='Sprites/port-icons.spr';ASSET=b.TARGET/'runtime'/REL
EXPECTED_ENTRY='fd7f59eae79ba5569400a8c10e0503126ff864ca3b05a436456787023cc5ce8c'
EXPECTED_ASSET='622f3d878f7ac17b14b52cd1438fdc51cc4f4c08f1f8227119802295184d83d9'
def install():
 idle();b.verify()
 if BACK.exists():raise RuntimeError('Preserve existing backup; do not install twice')
 assert b.sha(ENTRY)==EXPECTED_ENTRY and b.sha(ASSET)==EXPECTED_ASSET
 assert b.sha(b.TARGET/'runtime/Chaos-Wide169-engine.exe')=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 tests=json.loads((FIX/'ui-elements-verification.json').read_text(encoding='utf-8'))
 asset=json.loads((FIX/'asset-verification.json').read_text(encoding='utf-8'))
 assert tests['result']=='passed' and tests['qol_sha256']==b.sha(FIX/'qol_bindings.dll')
 assert asset['sha256']==b.sha(FIX/'port-icons.spr') and asset['frames']==234 and asset['exact_alpha']
 old=resources(ENTRY);new=resources(FIX/ENTRY.name)
 assert old[101]==new[101] and new[102]==(FIX/'qol_bindings.dll').read_bytes()
 originals={ENTRY:ENTRY.read_bytes(),ASSET:ASSET.read_bytes(),MANIFEST:MANIFEST.read_bytes()};before=b.inventory(b.TARGET/'runtime')
 BACK.mkdir()
 for p,data in originals.items():(BACK/p.name).write_bytes(data)
 m=json.loads(originals[MANIFEST]);m['launcher_sha256']=b.sha(FIX/ENTRY.name);m['files'][REL]=asset['sha256']
 m['portmanteau_ui_elements']=dict(module_sha256=tests['qol_sha256'],asset_sha256=asset['sha256'],frames=234,scope='page-only spell/item icons and independent UI tooltip viewport bounds',backup=str(BACK),acceptance='offline passed; paired runtime pending',battle_asset_unchanged=True)
 try:
  replace(ENTRY,(FIX/ENTRY.name).read_bytes());replace(ASSET,(FIX/'port-icons.spr').read_bytes());replace(MANIFEST,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
  after=b.inventory(b.TARGET/'runtime');assert set(after)==set(before);assert [n for n in before if before[n]!=after[n]]==[REL];b.verify()
 except BaseException:
  for p,data in originals.items():replace(p,data)
  raise
 b.write(BACK/'installation.json',dict(launcher_sha256=b.sha(ENTRY),before_launcher_sha256=EXPECTED_ENTRY,asset_sha256=b.sha(ASSET),before_asset_sha256=EXPECTED_ASSET,changed_runtime_files=[REL],engine_png_resource101_fullreadable_unchanged=True))
 print('Installed isolated UI elements:',ENTRY)
def rollback():
 idle();s=json.loads((BACK/'installation.json').read_text(encoding='utf-8'))
 assert b.sha(ENTRY)==s['launcher_sha256'] and b.sha(ASSET)==s['asset_sha256']
 assert b.sha(BACK/ENTRY.name)==s['before_launcher_sha256'] and b.sha(BACK/ASSET.name)==s['before_asset_sha256']
 for p in [ENTRY,ASSET,MANIFEST]:replace(p,(BACK/p.name).read_bytes())
 b.verify();print('Restored preceding map-fixed 1.1; saves untouched')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);globals()[p.parse_args().action]()
