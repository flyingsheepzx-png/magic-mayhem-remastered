"""Create immutable v7 package from the verified installed v6 package."""
import json
import shutil

from wide169_build import ROOT, BUILD, sha, write_json
from wide169_install import inventory, manifest, idle

idle()
state,prior=manifest()
parent=BUILD/'package-v6-realm-targets'
target=BUILD/'package-v7-dialog-grimoire-selection'
if target.exists() or parent.resolve()!=__import__('pathlib').Path(state['package']).resolve():
    raise RuntimeError('Unexpected package state')
shutil.copytree(parent/'runtime',target/'runtime')
assets=BUILD/'followup-assets'
for source in assets.rglob('*'):
    if source.is_file():
        destination=target/'runtime'/source.relative_to(assets)
        if not destination.is_file():raise RuntimeError('Unknown asset '+str(destination))
        shutil.copy2(source,destination)
engine=BUILD/'Chaos-Wide169-engine.exe'
launcher=ROOT/'modernization/build/Chaos-Wide169-Trial.exe'
shutil.copy2(engine,target/'runtime'/engine.name)
shutil.copy2(launcher,target/launcher.name)
spec=dict(kind='wide169-independent-package',parent_package=str(parent),
          engine_sha256=sha(engine.read_bytes()),files=inventory(target/'runtime'),
          launcher_sha256=sha(launcher.read_bytes()),native_canvas=[1280,720],
          output=[2560,1440],logic_preference=30)
write_json(target/'manifest.json',spec)
print(json.dumps({'package':str(target),'files':len(spec['files']),
                  'manifest_sha256':sha((target/'manifest.json').read_bytes()),
                  'launcher_sha256':spec['launcher_sha256'],'engine_sha256':spec['engine_sha256']},indent=2))
