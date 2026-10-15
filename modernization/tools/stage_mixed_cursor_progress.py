"""Back up and stage only the isolated cursor/loading candidate."""
import json
import shutil
import time
from PIL import Image
from compare_hd_baseline import ROOT, sha


def main():
    lab=ROOT/'modernization/playtests/mixed-ui-v4'
    manifest=lab/'manifest.json';m=json.loads(manifest.read_text(encoding='utf-8'))
    for name,digest in m['files'].items():
        if sha(lab/name)!=digest:raise RuntimeError('Package changed: '+name)
    backup=lab/('before-cursor-progress-'+time.strftime('%Y%m%d-%H%M%S'))
    backup.mkdir()
    updates={lab/'game-wide169/ddraw.dll':ROOT/'modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll',
             lab/'game/Chaos-Mixed-UI-Preview.exe':ROOT/'modernization/build/mixed-ui-v4-runtime/Chaos-Mixed-UI-Preview.exe'}
    bars=list((lab/'game-wide169/Interface/ProgressIndicator').glob('*.JPG'))
    paths=[*updates,*bars,manifest]
    for p in paths:
        target=backup/p.relative_to(lab);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    try:
        for p,source in updates.items():shutil.copy2(source,p)
        for p in bars:
            with Image.open(p) as im:
                if im.size!=(720,43):raise RuntimeError('Unexpected progress asset '+str(p))
                im.resize((1440,86),Image.Resampling.NEAREST).save(p,quality=100,subsampling=0)
        for p in paths[:-1]:m['files'][p.relative_to(lab).as_posix()]=sha(p)
        manifest.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
        (backup/'stage.json').write_text(json.dumps({'backup':str(backup),'files':{str(p.relative_to(lab)):sha(p) for p in paths[:-1]}},indent=2)+'\n',encoding='utf-8')
        print(backup)
    except BaseException:
        for p in paths:shutil.copy2(backup/p.relative_to(lab),p)
        raise


if __name__=='__main__':main()
