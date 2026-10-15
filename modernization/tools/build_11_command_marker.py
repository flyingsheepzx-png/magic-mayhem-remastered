"""Continue installed response-v1; restore native destination-effect lifecycle."""
import shutil,subprocess
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
b=base.b
OUT=b.ROOT/'modernization/build/remastered-1.1-command-response-v2'
OLD=b.ROOT/'modernization/build/remastered-1.1-command-response-v1'
assert resources(base.DEST/base.ENTRY)==resources(OLD/'release.exe')
OUT.mkdir(exist_ok=False)
for f in OLD.iterdir():
 if f.suffix in ('.cpp','.h','.inc','.rc','.ico','.dll') or f.name=='build.cmd':shutil.copy2(f,OUT/f.name)
shutil.copy2(b.SRC/'command_response.inc',OUT/'command_response.inc')
base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
