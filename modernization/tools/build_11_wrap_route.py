"""Preserve installed response-v2 and restore native toroidal route topology."""
import shutil,subprocess
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
b=base.b
OUT=b.ROOT/'modernization/build/remastered-1.1-wrap-route-v1'
OLD=b.ROOT/'modernization/build/remastered-1.1-command-response-v2'
assert resources(base.DEST/base.ENTRY)==resources(OLD/'release.exe')
OUT.mkdir(exist_ok=False)
for f in OLD.iterdir():
 if f.suffix in ('.cpp','.h','.inc','.rc','.ico','.dll') or f.name=='build.cmd':shutil.copy2(f,OUT/f.name)
shutil.copy2(b.SRC/'long_route.inc',OUT/'long_route.inc')
base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
