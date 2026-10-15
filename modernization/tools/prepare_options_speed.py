"""Prepare item3 without changing native speed save layout or battle timing hooks."""
import json,shutil,subprocess,re
import prepare_options_window as p
b=p.b;base=p.base
SOURCE=p.OUT
OUT=b.ROOT/'modernization/build/remastered-1.1-options-speed-v1'
BACK=b.ROOT/'modernization/backups/remastered-1.1-options-speed-v1'
SCREEN='Interface/BattleOptionsScreen/screen (Battle Options).cfg'
def build():
 current=p.resources(base.DEST/base.ENTRY);assert current==p.resources(SOURCE/'release.exe')
 rows=[]
 for e,m,k in base.targets():
  d=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==d['launcher_sha256'] and p.resources(e)==current
  assert b.sha(e.parent/'runtime/ddraw.dll')==b.sha(SOURCE/'wrapper/bin/Release/ddraw.dll')
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==d['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m),wrapper_sha256=b.sha(e.parent/'runtime/ddraw.dll')))
 OUT.mkdir(exist_ok=False);base.write(OUT/'before.json',rows)
 for f in SOURCE.iterdir():
  if f.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll']:shutil.copy2(f,OUT/f.name)
 shutil.copy2(b.SRC/'options_speed.cpp',OUT/'options_speed.cpp')
 f=OUT/'qol_bindings.cpp';s=f.read_text(encoding='utf-8');s=b.replace_once(s,'extern "C" bool mm_install_options_window();','extern "C" bool mm_install_options_window();\nextern "C" bool mm_install_options_speed();');s=b.replace_once(s,'return mm_install_options_window() &&','return mm_install_options_speed() && mm_install_options_window() &&');f.write_text(s,encoding='utf-8')
 f=OUT/'build.cmd';f.write_text(b.replace_once(f.read_text(),'options_window.cpp /link','options_window.cpp options_speed.cpp /link'))
 shutil.copytree(SOURCE/'wrapper',OUT/'wrapper')
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 assert all(p.resources(OUT/n)[i]==current[i] for n in ['candidate.exe','release.exe'] for i in [101,103])
 assert b.sha(OUT/'wrapper/bin/Release/ddraw.dll')==b.sha(SOURCE/'wrapper/bin/Release/ddraw.dll')
def label_bytes(raw):
 assert b'STR_95' not in raw
 return raw+b'\r\n'+b'\r\n'.join(('STR_'+str(k)+' = '+v).encode('gbk') for k,v in [(95,'快 40逻辑帧'),(96,'中 30逻辑帧'),(97,'慢 20逻辑帧')])+b'\r\n'
def screen_bytes(raw):
 for n,k in [(8,95),(9,96),(10,97)]:
  pattern=rb'(\[RADIOBUTTON_'+str(n).encode()+rb'\][\s\S]*?\bText=)\d+'
  raw,count=re.subn(pattern,lambda m:m[1]+str(k).encode(),raw);assert count==1
 return raw
def install():
 import install_options_resolution as i
 a=json.loads((OUT/'runtime-acceptance.json').read_text());assert a['result']=='passed' and a['candidate_sha256']==b.sha(OUT/'candidate.exe')
 base.write(OUT/'verification.json',dict(result='passed',module_sha256=b.sha(OUT/'qol_bindings.dll'),wrapper_sha256=b.sha(OUT/'wrapper/bin/Release/ddraw.dll'),runtime_acceptance=a))
 i.OUT=OUT;i.BACK=BACK;i.label_bytes=label_bytes;i.MANIFEST_FIELD='options_speed';i.EXTRA_RUNTIME_CHANGES=[(SCREEN,screen_bytes)];i.install()
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','install']);globals()[a.parse_args().action]()
