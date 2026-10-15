"""Current-module scanner regression, including previous preview recreation fix."""
from pathlib import Path
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'modernization/build/remastered-1.1-minimap-release'
p=ROOT/'modernization/tools/verify_11_minimap_center.py'
s=p.read_text().split('# Existing compiled scanner layout')[0]
s=s.replace("remastered-1.1-minimap-center'","remastered-1.1-minimap-release'")
exec(compile(s,str(p),'exec'))
click_checks=checks;old_mismatch=detected
p=ROOT/'modernization/tools/verify_11_minimap.py'
s=p.read_text().split('# Existing tooltip')[0]
s=s.replace("remastered-1.1-minimap-v2'","remastered-1.1-minimap-release'")
exec(compile(s,str(p),'exec'))
scanner_checks=checks
p=ROOT/'modernization/tools/verify_11_port_preview.py'
s=p.read_text().replace('remastered-1.1-port-preview','remastered-1.1-minimap-release')
exec(compile(s,str(p),'exec'))
v=json.loads((BUILD/'verification.json').read_text())
v.update(click_checks=click_checks,old_mismatch_cases=old_mismatch,scanner_checks=scanner_checks,
         scope='native click inverse, all rotations/storage widths; compiled scanner drawing and preview recreation retained')
# Guard the production source installation, not only the detached hook fixture.
source=(BUILD/'mixed_ui_fonts.cpp').read_text()
assert 'patch(0x555f1d,scanner_click_width_hook)' in source
assert 'memcmp((void*)0x555f1d' in source
(BUILD/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
print(v)
