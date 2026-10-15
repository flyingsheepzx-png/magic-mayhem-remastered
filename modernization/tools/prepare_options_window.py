"""Prepare sequential item2 from accepted options-resolution-v3."""
import json,shutil,subprocess,re,runpy
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
SOURCE=b.ROOT/'modernization/build/remastered-1.1-options-resolution-v3'
OUT=b.ROOT/'modernization/build/remastered-1.1-options-window-v1'
BACK=b.ROOT/'modernization/backups/remastered-1.1-options-window-v1'
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(SOURCE/'release.exe')
 rows=[]
 for e,m,k in base.targets():
  d=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==d['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/ddraw.dll')==b.sha(SOURCE/'wrapper/bin/Release/ddraw.dll')
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==d['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m),wrapper_sha256=b.sha(e.parent/'runtime/ddraw.dll')))
 OUT.mkdir(exist_ok=False);base.write(OUT/'before.json',rows)
 for f in SOURCE.iterdir():
  if f.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll']:shutil.copy2(f,OUT/f.name)
 shutil.copy2(b.SRC/'options_window.cpp',OUT/'options_window.cpp')
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8');s=b.replace_once(s,'extern "C" bool mm_install_options_resolution();','extern "C" bool mm_install_options_resolution();\nextern "C" bool mm_install_options_window();');s=b.replace_once(s,'return mm_install_options_resolution() &&','return mm_install_options_window() && mm_install_options_resolution() &&');p.write_text(s,encoding='utf-8')
 p=OUT/'build.cmd';p.write_text(b.replace_once(p.read_text(),'options_resolution.cpp /link','options_resolution.cpp options_window.cpp /link'))
 ws=OUT/'wrapper';shutil.copytree(SOURCE/'wrapper',ws,ignore=shutil.ignore_patterns('bin','obj','Debug','Release','.vs'))
 h=(b.SRC/'display_resolution.h').read_text();(ws/'src/display_resolution.h').write_text(h);(ws/'src/display_resolution_load.h').write_text(h[:h.index('static UINT mm_display_message')]+'\n#endif\n')
 p=ws/'src/wndproc.c';s=p.read_text();s=b.replace_once(s,'    if(uMsg==mm_display_message()', '    if(uMsg==mm_display_window_message() && mm_mixed_enabled())return mm_display_apply_window(wParam,lParam);\n    if(uMsg==mm_display_message()');p.write_text(s)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 assert all(resources(OUT/name)[i]==current[i] for name in ['candidate.exe','release.exe'] for i in [101,103])
 subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
def label_bytes(raw):
 for k,value in [(17,'窗口模式'),(24,'窗口化'),(25,'无边框窗口化')]:
  raw,n=re.subn(rb'(?m)^(STR_'+str(k).encode()+rb'\s*=\s*)[^\r\n]*',lambda m:m[1]+value.encode('gbk'),raw);assert n==1
 return raw
def install():
 import install_options_resolution as i
 acceptance=json.loads((OUT/'runtime-acceptance.json').read_text());assert acceptance['result']=='passed' and acceptance['wrapper_sha256']==b.sha(OUT/'wrapper/bin/Release/ddraw.dll')
 base.write(OUT/'verification.json',dict(result='passed',module_sha256=b.sha(OUT/'qol_bindings.dll'),wrapper_sha256=b.sha(OUT/'wrapper/bin/Release/ddraw.dll'),runtime_acceptance=acceptance))
 i.OUT=OUT;i.BACK=BACK;i.label_bytes=label_bytes;i.MANIFEST_FIELD='options_window';i.install()
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install']);globals()[p.parse_args().action]()
