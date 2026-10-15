"""Repair resolution transport, retaining current installed modules and wrapper."""
import json,shutil,subprocess
import prepare_options_resolution as p
from install_11_minimap_v2 import resources
OUT=p.b.ROOT/'modernization/build/remastered-1.1-options-resolution-v3'
def build():
 source=p.OUT;rows=[]
 current=resources(p.base.DEST/p.base.ENTRY)
 assert current==resources(source/'release.exe')
 for e,m,k in p.base.targets():
  d=json.loads(m.read_text(encoding='utf-8'))
  assert p.b.sha(e)==d['launcher_sha256'] and resources(e)==current
  assert p.b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==d['engine_sha256']== '42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  assert p.b.sha(e.parent/'runtime/ddraw.dll')==p.b.sha(source/'wrapper/bin/Release/ddraw.dll')
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=p.b.sha(e),manifest_sha256=p.b.sha(m),wrapper_sha256=p.b.sha(e.parent/'runtime/ddraw.dll')))
 OUT.mkdir(exist_ok=False)
 for f in source.iterdir():
  if f.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll']:shutil.copy2(f,OUT/f.name)
 p.base.write(OUT/'before.json',rows)
 shutil.copy2(p.b.SRC/'options_resolution.cpp',OUT/'options_resolution.cpp')
 ws=OUT/'wrapper';shutil.copytree(source/'wrapper',ws,ignore=shutil.ignore_patterns('bin','obj','Debug','Release','.vs'))
 shutil.copy2(p.b.SRC/'display_resolution.h',ws/'src/display_resolution.h')
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 assert all(resources(OUT/name)[i]==current[i] for name in ['candidate.exe','release.exe'] for i in [101,103])
 subprocess.run([str(p.b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
def verify():
 import runpy
 p.OUT=OUT
 runpy.run_path(str(p.b.ROOT/'modernization/tests/options_resolution_test.py'),run_name='__main__')
def install():
 import install_options_resolution as installer
 evidence=p.b.ROOT/'modernization/logs/remastered-ui/options-resolution-acceptance-v3/acceptance.json'
 acceptance=json.loads(evidence.read_text())
 assert acceptance['result']=='passed' and acceptance['wrapper_sha256']==p.b.sha(OUT/'wrapper/bin/Release/ddraw.dll')
 v=json.loads((OUT/'verification.json').read_text())
 v['runtime_acceptance']=acceptance;v['runtime_evidence']=str(evidence)
 p.base.write(OUT/'verification.json',v)
 installer.OUT=OUT;installer.BACK=p.b.ROOT/'modernization/backups/remastered-1.1-options-resolution-v3'
 installer.install()
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','verify','install']);args=parser.parse_args()
 globals()[args.action]()
