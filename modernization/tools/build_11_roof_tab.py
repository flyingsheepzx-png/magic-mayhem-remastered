"""One iteration: Tab invokes native roof control, preserving current input fix."""
import argparse,json,shutil,subprocess
import build_11_main_portrait_cancel as prev
from install_11_minimap_v2 import resources
b=prev.b;base=prev.base
OUT=b.ROOT/'modernization/build/remastered-1.1-roof-tab'
BACK=b.ROOT/'modernization/backups/remastered-1.1-roof-tab'
SOURCE=prev.OUT
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(SOURCE/'release.exe')
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll'):shutil.copy2(p,OUT/p.name)
 shutil.copy2(b.SRC/'roof_tab.inc',OUT/'roof_tab.inc')
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
 s=b.replace_once(s,'unsigned battle_resume=0x46c19a', '#include "roof_tab.inc"\nunsigned battle_resume=0x46c19a')
 old='__declspec(naked) void battle_key_hook(){__asm{\n    pushfd\n    pushad\n'
 s=b.replace_once(s,old,old+'''    mov eax,[esp+34h]
    push eax
    mov eax,[esp+5ch]
    push eax
    push esi
    call roof_tab
    add esp,12
    test eax,eax
    jnz consumed
''')
 p.write_text(s,encoding='utf-8');base.write(OUT/'before.json',rows)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True);verify()
def verify():
 current=resources(SOURCE/'release.exe')
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert set(r)==set(current)
  assert all(r[i]==((OUT/'qol_bindings.dll').read_bytes() if i==102 else current[i]) for i in current)
 for p in SOURCE.iterdir():
  if p.suffix in ('.cpp','.h','.inc') and p.name!='qol_bindings.cpp':assert p.read_bytes()==(OUT/p.name).read_bytes(),p.name
def install():
 verify();v=json.loads((OUT/'verification.json').read_text())
 assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'qol_bindings.dll')
 base.OUT=OUT;base.BACK=BACK;base.install('roof_tab_shortcut')
 for e,m,k in base.targets():assert resources(e)==resources(OUT/('candidate.exe' if k=='candidate' else 'release.exe'))
def rollback():
 base.OUT=OUT;base.BACK=BACK;base.rollback()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
